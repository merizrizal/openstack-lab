package main

import (
	"fmt"
	"io"
	"os"
)

const unavailableReason = "mandatory diagnostic safety controls are not implemented"

func main() {
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}

func run(args []string, stdout, stderr io.Writer) int {
	if len(args) == 0 {
		printHelp(stdout)
		return 0
	}

	switch args[0] {
	case "help", "-h", "--help":
		printHelp(stdout)
		return 0
	case "readiness", "ready":
		fmt.Fprintf(stdout, "status=unavailable: %s\n", unavailableReason)
		return 1
	case "catalog":
		fmt.Fprintf(stdout, "diagnostics=unavailable: %s\n", unavailableReason)
		return 0
	case "diagnostic", "diagnose", "run":
		fmt.Fprintf(stderr, "diagnostic unavailable: %s\n", unavailableReason)
		return 2
	default:
		fmt.Fprintf(stderr, "diagnostic unavailable: no diagnostic command is enabled (%q)\n", args[0])
		return 2
	}
}

func printHelp(stdout io.Writer) {
	fmt.Fprintln(stdout, "AI-OPS Go — dormant local runtime")
	fmt.Fprintln(stdout, "Usage: aiops <help|readiness|catalog|diagnose>")
	fmt.Fprintln(stdout, "Help, readiness, and catalog are local-only.")
	fmt.Fprintf(stdout, "Diagnostic execution is unavailable: %s.\n", unavailableReason)
}
