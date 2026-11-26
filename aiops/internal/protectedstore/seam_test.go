//go:build linux && amd64

package protectedstore

import (
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
)

func parseProductionFiles(t *testing.T) (*token.FileSet, []*ast.File) {
	t.Helper()
	paths, err := filepath.Glob("*.go")
	if err != nil {
		t.Fatal(err)
	}
	fset := token.NewFileSet()
	var files []*ast.File
	for _, p := range paths {
		if strings.HasSuffix(p, "_test.go") {
			continue
		}
		f, err := parser.ParseFile(fset, p, nil, 0)
		if err != nil {
			t.Fatal(err)
		}
		files = append(files, f)
	}
	if len(files) == 0 {
		t.Fatal("no production files parsed")
	}
	return fset, files
}

// Production construction cannot reach the test-only options seam or the
// fault seam: the exported constructors pass productionMounts() and nil, the
// only production mountOptionSource is procMountSource, and holder seams are
// assigned only from forwarded parameters.
func TestProductionConstructionCannotReachTestSeams(t *testing.T) {
	if _, ok := productionMounts().(procMountSource); !ok {
		t.Fatal("productionMounts does not return the /proc source")
	}
	_, files := parseProductionFiles(t)
	// Every exported constructor is a single forwarding return that binds only
	// the production mount source, the production capacity checker (when it
	// takes one) and a nil fault seam.
	type ctorRule struct {
		inner string
		args  []string
	}
	exported := map[string]ctorRule{
		"Initialize":    {"initialize", []string{"cfg", "productionMounts()", "nil"}},
		"OpenBootstrap": {"openBootstrap", []string{"cfg", "productionMounts()", "nil"}},
		"OpenSession":   {"openSession", []string{"cfg", "productionMounts()", "productionCapacity()", "nil"}},
	}
	found := map[string]bool{}
	implementers := map[string]map[string]bool{}
	for _, file := range files {
		for _, decl := range file.Decls {
			fn, ok := decl.(*ast.FuncDecl)
			if !ok {
				continue
			}
			if fn.Recv != nil && (fn.Name.Name == "mountInfo" || fn.Name.Name == "ext4Options") {
				recv := typeName(fn.Recv.List[0].Type)
				if implementers[recv] == nil {
					implementers[recv] = map[string]bool{}
				}
				implementers[recv][fn.Name.Name] = true
			}
			rule, isExported := exported[fn.Name.Name]
			if !isExported || fn.Recv != nil {
				continue
			}
			found[fn.Name.Name] = true
			if len(fn.Body.List) != 1 {
				t.Fatalf("%s must be a single forwarding return", fn.Name.Name)
			}
			ret, ok := fn.Body.List[0].(*ast.ReturnStmt)
			if !ok || len(ret.Results) != 1 {
				t.Fatalf("%s must return the internal constructor result", fn.Name.Name)
			}
			call, ok := ret.Results[0].(*ast.CallExpr)
			if !ok || exprName(call.Fun) != rule.inner || len(call.Args) != len(rule.args) {
				t.Fatalf("%s must call %s(%s)", fn.Name.Name, rule.inner, strings.Join(rule.args, ", "))
			}
			for i, want := range rule.args {
				if got := renderArg(call.Args[i]); got != want {
					t.Fatalf("%s argument %d is %q, want %q", fn.Name.Name, i, got, want)
				}
			}
		}
	}
	for name := range exported {
		if !found[name] {
			t.Fatalf("exported constructor %s not found", name)
		}
	}
	if len(implementers) != 1 || !implementers["procMountSource"]["mountInfo"] || !implementers["procMountSource"]["ext4Options"] {
		t.Fatalf("production mountOptionSource implementers = %v, want only procMountSource", implementers)
	}

	// Seam fields are only ever set from the forwarded constructor parameters.
	for _, file := range files {
		ast.Inspect(file, func(n ast.Node) bool {
			switch x := n.(type) {
			case *ast.KeyValueExpr:
				key := exprName(x.Key)
				if (key == "mounts" && exprName(x.Value) != "src") || (key == "hooks" && exprName(x.Value) != "hooks") {
					t.Errorf("holder seam %s set from %s in production code", key, exprName(x.Value))
				}
			case *ast.AssignStmt:
				for _, lhs := range x.Lhs {
					if sel, ok := lhs.(*ast.SelectorExpr); ok && (sel.Sel.Name == "mounts" || sel.Sel.Name == "hooks") {
						t.Errorf("holder seam %s reassigned in production code", sel.Sel.Name)
					}
				}
			}
			return true
		})
	}
}

// Static X review supplement: no diagnostic, network, SDK, exec or legacy
// store import, and no golang.org/x/sys dependency.
func TestPackageImportBoundary(t *testing.T) {
	_, files := parseProductionFiles(t)
	allowed := map[string]bool{
		"bytes": true, "crypto/sha256": true, "encoding/binary": true, "encoding/hex": true,
		"encoding/json": true, "errors": true, "fmt": true, "io": true, "os": true,
		"path/filepath": true, "regexp": true, "strconv": true, "strings": true, "sync": true,
		"syscall": true, "time": true, "unicode/utf8": true, "unsafe": true,
	}
	for _, file := range files {
		for _, imp := range file.Imports {
			path, _ := strconv.Unquote(imp.Path.Value)
			if !allowed[path] {
				t.Errorf("production import %q is outside the reviewed standard-library set", path)
			}
		}
	}
	mod, err := os.ReadFile(filepath.Join("..", "..", "go.mod"))
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(mod), "golang.org/x/sys") {
		t.Fatal("go.mod gained golang.org/x/sys")
	}
}

func typeName(e ast.Expr) string {
	switch x := e.(type) {
	case *ast.StarExpr:
		return typeName(x.X)
	case *ast.Ident:
		return x.Name
	}
	return ""
}

func exprName(e ast.Expr) string {
	switch x := e.(type) {
	case *ast.Ident:
		return x.Name
	case *ast.SelectorExpr:
		return exprName(x.X) + "." + x.Sel.Name
	}
	return ""
}

// renderArg renders an argument as an identifier, a selector or a call with no
// arguments, so a constructor's forwarded arguments can be compared exactly.
func renderArg(e ast.Expr) string {
	if call, ok := e.(*ast.CallExpr); ok {
		if len(call.Args) != 0 {
			return "call-with-arguments"
		}
		return exprName(call.Fun) + "()"
	}
	return exprName(e)
}

// funcsOf calls visit for every production function body with its receiver
// type name ("" for plain functions).
func funcsOf(files []*ast.File, visit func(fn *ast.FuncDecl, recv string)) {
	for _, file := range files {
		for _, decl := range file.Decls {
			fn, ok := decl.(*ast.FuncDecl)
			if !ok || fn.Body == nil {
				continue
			}
			recv := ""
			if fn.Recv != nil {
				recv = typeName(fn.Recv.List[0].Type)
			}
			visit(fn, recv)
		}
	}
}

// returnsOf collects every return statement of fn, not descending into
// function literals.
func returnsOf(fn *ast.FuncDecl) []*ast.ReturnStmt {
	var out []*ast.ReturnStmt
	ast.Inspect(fn.Body, func(n ast.Node) bool {
		switch x := n.(type) {
		case *ast.FuncLit:
			return false
		case *ast.ReturnStmt:
			out = append(out, x)
		}
		return true
	})
	return out
}

func isNilIdent(e ast.Expr) bool {
	id, ok := e.(*ast.Ident)
	return ok && id.Name == "nil"
}

// callPositions returns the position of the first call to each name (matched
// on the final selector element) in fn, in source order of first occurrence.
func callPositions(fn *ast.FuncDecl, names ...string) map[string]token.Pos {
	want := map[string]bool{}
	for _, n := range names {
		want[n] = true
	}
	out := map[string]token.Pos{}
	ast.Inspect(fn.Body, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}
		name := exprName(call.Fun)
		if i := strings.LastIndex(name, "."); i >= 0 {
			name = name[i+1:]
		}
		if _, seen := out[name]; want[name] && !seen {
			out[name] = call.Pos()
		}
		return true
	})
	return out
}

// requireOrderedCalls fails unless fn calls every name, and the first calls
// occur in the order given.
func requireOrderedCalls(t *testing.T, fn *ast.FuncDecl, names ...string) {
	t.Helper()
	pos := callPositions(fn, names...)
	last := token.NoPos
	for _, name := range names {
		p, ok := pos[name]
		if !ok {
			t.Errorf("%s never calls %s", fn.Name.Name, name)
			continue
		}
		if p < last {
			t.Errorf("%s calls %s out of order", fn.Name.Name, name)
		}
		last = p
	}
}

// Production admission is closed to anything but the real check: the startup
// capacity seam has exactly one production implementation, realCapacity, which
// has no success path of its own (it forwards the holder's real check); the
// only success in the real check is the final statement of decideCapacity,
// after every identity, managed, filesystem and quota step; the seam is bound
// only by the exported constructor, consulted only inside openSession and
// before the ACTIVE commit, and never stored in a type; the only production
// path to a record write is through a Session, which is constructed only after
// the durable ACTIVE write.
func TestProductionAdmissionSeamsAreClosed(t *testing.T) {
	fset, files := parseProductionFiles(t)

	var implementers []string
	funcsOf(files, func(fn *ast.FuncDecl, recv string) {
		if recv != "" && fn.Name.Name == "checkBeforeActive" {
			implementers = append(implementers, recv)
		}
	})
	if len(implementers) != 1 || implementers[0] != "realCapacity" {
		t.Fatalf("production capacity checkers = %v, want only realCapacity", implementers)
	}

	seen := map[string]bool{}
	funcsOf(files, func(fn *ast.FuncDecl, recv string) {
		name := fn.Name.Name
		line := func(n ast.Node) int { return fset.Position(n.Pos()).Line }
		switch {
		case name == "productionCapacity" && recv == "":
			seen[name] = true
			ret, ok := fn.Body.List[len(fn.Body.List)-1].(*ast.ReturnStmt)
			if !ok || len(fn.Body.List) != 1 || len(ret.Results) != 1 {
				t.Fatal("productionCapacity must be a single return")
			}
			lit, ok := ret.Results[0].(*ast.CompositeLit)
			if !ok || exprName(lit.Type) != "realCapacity" {
				t.Fatal("productionCapacity must return realCapacity{}")
			}
		case name == "checkBeforeActive" && recv == "realCapacity":
			seen[name] = true
			// Every return is a refusal or the holder's real check; none is nil.
			for _, ret := range returnsOf(fn) {
				allowed := false
				if len(ret.Results) == 1 {
					if call, isCall := ret.Results[0].(*ast.CallExpr); isCall {
						callee := exprName(call.Fun)
						allowed = callee == "refuse" || callee == "req.holder.checkCapacity"
					}
				}
				if !allowed {
					t.Errorf("realCapacity.checkBeforeActive may return only a refusal or req.holder.checkCapacity() (line %d)", line(ret))
				}
			}
		case name == "checkCapacity" && recv == "holder":
			seen[name] = true
			rets := returnsOf(fn)
			for _, ret := range rets {
				if len(ret.Results) != 1 || isNilIdent(ret.Results[0]) {
					t.Errorf("holder.checkCapacity may not return nil itself (line %d)", line(ret))
				}
			}
			last, ok := fn.Body.List[len(fn.Body.List)-1].(*ast.ReturnStmt)
			if !ok {
				t.Fatal("holder.checkCapacity must end by returning the decision")
			}
			if call, isCall := last.Results[0].(*ast.CallExpr); !isCall || exprName(call.Fun) != "decideCapacity" {
				t.Fatal("holder.checkCapacity must end by returning decideCapacity(...)")
			}
			requireOrderedCalls(t, fn, "observeIdentity", "checkBinding", "deriveNeed", "accountManaged", "decideCapacity")
		case name == "decideCapacity" && recv == "":
			seen[name] = true
			rets := returnsOf(fn)
			for i, ret := range rets {
				last := i == len(rets)-1
				if len(ret.Results) != 1 || isNilIdent(ret.Results[0]) != last {
					t.Errorf("decideCapacity may return nil only as its final statement (line %d)", line(ret))
				}
			}
			if final, ok := fn.Body.List[len(fn.Body.List)-1].(*ast.ReturnStmt); !ok || !isNilIdent(final.Results[0]) {
				t.Error("decideCapacity must end with its single success return")
			}
			requireOrderedCalls(t, fn, "checkBinding", "checkManaged", "checkFilesystem", "checkQuotaHeadroom")
		}
	})
	for _, name := range []string{"productionCapacity", "checkBeforeActive", "checkCapacity", "decideCapacity"} {
		if !seen[name] {
			t.Errorf("guardrail did not find %s", name)
		}
	}

	// No other production function may produce a capacity success: apart from
	// decideCapacity's final return, nothing named like a checker returns a bare nil.
	funcsOf(files, func(fn *ast.FuncDecl, recv string) {
		if fn.Name.Name != "checkBeforeActive" {
			return
		}
		for _, ret := range returnsOf(fn) {
			if len(ret.Results) == 1 && isNilIdent(ret.Results[0]) {
				t.Errorf("%s.checkBeforeActive returns nil", recv)
			}
		}
	})

	// The checker is consulted, and openSession is entered, from one place each.
	funcsOf(files, func(fn *ast.FuncDecl, recv string) {
		for _, field := range fn.Type.Params.List {
			if typeName(field.Type) == "capacityChecker" && fn.Name.Name != "openSession" {
				t.Errorf("%s accepts a capacityChecker; only openSession may", fn.Name.Name)
			}
		}
		ast.Inspect(fn.Body, func(n ast.Node) bool {
			call, ok := n.(*ast.CallExpr)
			if !ok {
				return true
			}
			switch name := exprName(call.Fun); {
			case strings.HasSuffix(name, ".checkBeforeActive") && fn.Name.Name != "openSession":
				t.Errorf("%s consults the capacity seam; only openSession may", fn.Name.Name)
			case name == "openSession" && fn.Name.Name != "OpenSession":
				t.Errorf("%s calls openSession; only OpenSession may", fn.Name.Name)
			case (strings.HasSuffix(name, ".commitRecord") || strings.HasSuffix(name, ".readRecord")) && recv != "Session":
				t.Errorf("%s writes or reads records outside a Session", fn.Name.Name)
			}
			return true
		})
	})
	for _, file := range files {
		ast.Inspect(file, func(n ast.Node) bool {
			if ts, ok := n.(*ast.TypeSpec); ok {
				if st, ok := ts.Type.(*ast.StructType); ok {
					for _, field := range st.Fields.List {
						if typeName(field.Type) == "capacityChecker" {
							t.Errorf("type %s stores a capacityChecker", ts.Name.Name)
						}
					}
				}
			}
			return true
		})
	}

	// A Session is constructed in exactly one place, strictly after the call
	// that durably commits ACTIVE.
	literals, commitAt := 0, token.NoPos
	funcsOf(files, func(fn *ast.FuncDecl, recv string) {
		ast.Inspect(fn.Body, func(n ast.Node) bool {
			switch x := n.(type) {
			case *ast.CompositeLit:
				if exprName(x.Type) == "Session" {
					literals++
					if fn.Name.Name != "openSession" || commitAt == token.NoPos || x.Pos() < commitAt {
						t.Errorf("Session constructed in %s (line %d) outside openSession or before the ACTIVE commit", fn.Name.Name, fset.Position(x.Pos()).Line)
					}
				}
			case *ast.CallExpr:
				if fn.Name.Name == "openSession" && strings.HasSuffix(exprName(x.Fun), ".commitActive") && commitAt == token.NoPos {
					commitAt = x.Pos()
				}
			}
			return true
		})
	})
	if literals != 1 {
		t.Fatalf("found %d Session constructions, want exactly 1", literals)
	}

	// The real check runs strictly before the first ACTIVE write.
	checked := false
	funcsOf(files, func(fn *ast.FuncDecl, recv string) {
		if fn.Name.Name == "openSession" && recv == "" {
			checked = true
			requireOrderedCalls(t, fn, "classifyControl", "verified", "checkBeforeActive", "commitActive")
		}
	})
	if !checked {
		t.Fatal("openSession not found")
	}
}

// A Session offers no record, dispatch or request method. Everything beyond
// these four is a deliberate, reviewed extension.
func TestSessionOffersOnlyLeaseAndHealthMethods(t *testing.T) {
	typ := reflect.TypeOf(&Session{})
	allowed := map[string]bool{"Info": true, "CheckBeforeAdmission": true, "CloseOrderly": true, "Release": true}
	for i := 0; i < typ.NumMethod(); i++ {
		if name := typ.Method(i).Name; !allowed[name] {
			t.Fatalf("Session exposes unexpected method %s", name)
		}
	}
	if typ.NumMethod() != len(allowed) {
		t.Fatalf("Session exposes %d methods, want %d", typ.NumMethod(), len(allowed))
	}
}
