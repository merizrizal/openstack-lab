The best way to learn **AI engineering from zero** is not to begin with “multi-agent systems” or complicated frameworks. Start by understanding what an LLM actually does, then progressively build the machinery around it that turns it into an agent capable of handling projects and tasks.

A useful mental model is:

```text
AI Engineering
│
├── LLM fundamentals
├── Prompting / structured output
├── Tool calling
├── Agent loop
├── Context and memory
├── RAG / knowledge retrieval
├── Workflow orchestration
├── Multi-agent systems
├── Evaluation
├── Safety / guardrails
├── Observability
└── Production deployment
```

And importantly:

```text
LLM ≠ Agent
Agent ≠ Multi-Agent System
Agent ≠ Workflow
```

Those distinctions are some of the first things you should understand.

## The learning roadmap I recommend

I'd organize your learning into roughly **12 stages**.

### Stage 0 — Build the mental model

Before writing code, understand these concepts:

```text
LLM
Prompt
Context window
Tokens
Inference
System prompt
Structured output
Tool calling
Agent
Workflow
Orchestrator
State
Memory
RAG
MCP
Evaluation
Guardrails
```

At this point, you should be able to explain a basic AI application like this:

```text
User
  │
  ▼
Application
  │
  ▼
LLM
  │
  ├── answer directly
  │
  └── request a tool
          │
          ▼
        Tool
          │
          ▼
       Result
          │
          ▼
         LLM
          │
          ▼
        User
```

No agents yet.

---

# Stage 1 — Learn how an LLM application works

Build something extremely simple:

```text
terminal
   │
   ▼
your program
   │
   ▼
LLM API
   │
   ▼
response
```

For example:

```text
$ ai "Explain this Java exception"

AI:
The NullPointerException occurs because...
```

The point isn't the application itself.

You're learning:

```text
messages
system instructions
user instructions
model responses
temperature
tokens
context
API requests
API responses
```

At this stage your program is **not an agent**.

It is basically:

```python
response = model.ask(user_message)
print(response)
```

---

# Stage 2 — Structured output

Then stop treating the model as a text generator.

Make it produce data.

Instead of:

```text
I think this problem is probably related to networking.
```

you want something like:

```json
{
  "category": "network",
  "severity": "high",
  "recommended_action": "inspect neutron logs"
}
```

This is extremely important in AI engineering.

Why?

Because machines need predictable output.

Later your orchestration system might do:

```text
LLM result
    │
    ├── network → network diagnostic workflow
    ├── storage → storage diagnostic workflow
    ├── compute → compute diagnostic workflow
    └── unknown → ask human
```

You're beginning to combine:

```text
probabilistic AI
       +
deterministic software
```

That combination is at the heart of good AI engineering.

---

# Stage 3 — Tool calling

Now things become interesting.

Give the model capabilities.

For example:

```text
Tools:

get_server_status(server_id)
get_nova_logs(server_id)
get_neutron_ports(server_id)
get_hypervisor_status(host)
```

The model doesn't execute them itself.

Instead:

```text
User:
Why can't VM-123 boot?

          │
          ▼

LLM:
I should inspect the VM.

Tool call:
get_server_status("VM-123")

          │
          ▼

Your program executes it.

          │
          ▼

Tool result:
status=ERROR
fault="No valid host"

          │
          ▼

LLM:
I should inspect compute capacity.

Tool call:
get_hypervisor_status(...)
```

Now the AI can **act through your software**.

This is one of the foundations of agents.

---

# Stage 4 — Understand the agent loop

An agent isn't magic.

A simplified agent is basically a loop:

```text
                ┌─────────────────────┐
                │        Goal         │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │      Observe        │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │       Reason        │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Choose next action  │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Execute tool     │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Observe the result  │
                └──────────┬──────────┘
                           │
                     goal complete?
                      /          \
                    no            yes
                    │              │
                    └──── loop ────┘
```

For example:

```text
Goal:
Investigate why VM-123 cannot boot.

Agent:
1. inspect server
2. inspect fault
3. inspect scheduler
4. inspect compute capacity
5. correlate findings
6. produce diagnosis
```

That's already an agent.

You don't need five AI agents talking to each other.

---

# Stage 5 — State, context and memory

Now you'll encounter a major engineering problem.

Suppose an agent is investigating something for 40 steps.

It needs to remember:

```text
Goal
Current hypothesis
Actions already executed
Results
Failed approaches
Important discoveries
User constraints
```

So your agent might maintain state:

```json
{
  "goal": "investigate VM-123",
  "status": "investigating",
  "hypotheses": [
    "compute capacity exhausted"
  ],
  "completed_tasks": [
    "inspect_server",
    "inspect_scheduler"
  ],
  "evidence": [
    "scheduler returned NoValidHost"
  ]
}
```

This leads to concepts such as:

```text
conversation memory
working memory
persistent memory
project state
task state
checkpoints
summarization
```

This area is far more important than people initially expect.

---

# Stage 6 — RAG and knowledge

Agents often need information that isn't inside the model.

For example:

```text
Company runbooks
Architecture documents
Git repository
tickets
logs
incident reports
API documentation
```

You don't want to stuff everything into the prompt.

Instead:

```text
Question
   │
   ▼
Retriever
   │
   ▼
Find relevant documents
   │
   ▼
Provide relevant context
   │
   ▼
LLM
```

This is commonly called **Retrieval-Augmented Generation — RAG**.

You'll eventually learn:

```text
embeddings
vector databases
chunking
retrieval
reranking
metadata filtering
hybrid search
```

But don't begin here.

---

# Stage 7 — Workflow orchestration

This is particularly relevant to your question about:

> orchestrate agent to handle project, tasks, etc.

Imagine asking an AI:

```text
Implement feature X.
```

A naïve agent might just start modifying files.

A better system creates a workflow.

```text
                      PROJECT
                         │
                         ▼
                   Analyze goal
                         │
                         ▼
                  Create task plan
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
   Task A             Task B             Task C
   research           backend            tests
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                     Review
                         │
                         ▼
                    Validation
                         │
                         ▼
                     Complete
```

The important idea is that **the orchestrator owns the workflow**.

Not the LLM.

For example:

```text
ProjectOrchestrator

create_plan()
     ↓
execute_task()
     ↓
validate_task()
     ↓
update_project_state()
     ↓
select_next_task()
     ↓
repeat
```

The LLM helps make decisions inside this system.

---

# Stage 8 — Task graphs

Eventually you'll discover that projects aren't just lists.

They have dependencies.

Example:

```text
Task A: design DB schema
   │
   ├────► Task B: implement repository
   │
   └────► Task C: create migrations
              │
              ▼
         Task D: integration tests
              │
              ▼
         Task E: deployment
```

This is a **task graph**, often represented as a DAG:

> Directed Acyclic Graph.

An orchestrator may maintain something like:

```json
{
  "tasks": [
    {
      "id": "A",
      "status": "completed"
    },
    {
      "id": "B",
      "depends_on": ["A"],
      "status": "ready"
    },
    {
      "id": "C",
      "depends_on": ["A"],
      "status": "ready"
    },
    {
      "id": "D",
      "depends_on": ["B", "C"],
      "status": "blocked"
    }
  ]
}
```

Notice something important.

Most of this isn't AI.

It's ordinary software engineering.

That is one of the biggest lessons in AI engineering.

---

# Stage 9 — Agent orchestration

Only after understanding workflows should you introduce multiple agents.

You might have:

```text
                  Orchestrator
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   Researcher       Developer        Reviewer
      Agent            Agent           Agent
       │               │               │
       ▼               ▼               ▼
  Search docs       Modify code      Inspect work
```

But I want you to be careful here.

A common beginner assumption is:

```text
More agents = better system
```

Usually, no.

Multiple agents create new problems:

```text
coordination
duplicate work
conflicting decisions
large token usage
long execution
context synchronization
error propagation
deadlocks
poor observability
```

Often:

```text
1 capable agent
+
good tools
+
good workflow
+
good state management
```

is better than:

```text
10 agents chatting with each other
```

---

# Stage 10 — Evaluation

This is where AI engineering starts looking like real engineering rather than experimentation.

How do you know your agent is good?

You need tests.

For example:

```text
Test scenario:
VM reports NoValidHost.

Expected agent behavior:

✓ inspect Nova scheduler
✓ inspect compute capacity
✓ inspect placement
✗ must NOT restart Nova
✗ must NOT modify OpenStack
✓ cite evidence
✓ produce diagnosis
```

Then measure:

```text
task success rate
tool selection accuracy
hallucination rate
number of unnecessary tool calls
latency
token cost
safety violations
```

This is called **AI evaluation / evals**.

It is an extremely important subject.

---

# Stage 11 — Guardrails and safety

Once agents can perform actions, you need boundaries.

For example:

```text
                  Agent
                    │
                    ▼
                Tool request
                    │
                    ▼
            Permission policy
              /           \
        permitted        denied
           │                │
           ▼                ▼
       execute          reject
```

Possible categories:

```text
read operation     → automatically allowed
safe write         → maybe allowed
dangerous write    → human approval
destructive        → prohibited
```

For infrastructure, you might start with:

```text
GET information        ✓
read logs              ✓
query databases        ✓ read-only

restart service        ✗
delete VM              ✗
modify networking      ✗
change configuration   ✗
```

This is how we can eventually connect agents to real infrastructure safely.

---

# Stage 12 — Production AI engineering

Only now do we assemble everything.

A production architecture might eventually look like:

```text
                           User
                             │
                             ▼
                       Chat / CLI / API
                             │
                             ▼
                    ┌──────────────────┐
                    │   Orchestrator   │
                    └────────┬─────────┘
                             │
               ┌─────────────┼─────────────┐
               │             │             │
               ▼             ▼             ▼
          Agent runtime    Project       Scheduler
                           state
               │             │
               ▼             ▼
             Tools          DB
               │
        ┌──────┼────────┬────────┐
        ▼      ▼        ▼        ▼
      Git    MCP     Search    APIs
        │      │        │        │
        └──────┴────────┴────────┘

                     + Observability
                     + Audit logs
                     + Evaluation
                     + Guardrails
                     + Human approval
```

At this point you are doing actual **AI engineering**, rather than simply calling an LLM API.

---

## Where MCP fits

You've encountered MCP before, but I would deliberately place it relatively late in this learning journey.

MCP stands for **Model Context Protocol**.

Think of it approximately as a standard interface between an AI client and external capabilities:

```text
Agent / AI Client
        │
       MCP
        │
   ┌────┼─────┐
   ▼    ▼     ▼
 files  logs  OpenStack
```

Without MCP you might implement:

```python
agent.register_tool(get_vm_status)
agent.register_tool(read_nova_logs)
```

With MCP, those capabilities can be exposed through a standardized server interface.

MCP is useful.

But MCP itself does **not** teach you how agents work.

That's why I would learn:

```text
LLM
 ↓
structured output
 ↓
tool calling
 ↓
agent loop
 ↓
state
 ↓
workflow
 ↓
orchestration
 ↓
MCP
```

rather than starting with MCP.

---

# One especially important distinction

Over the course of learning, I want you to distinguish these four concepts very clearly.

### 1. Model

For example:

```text
GPT
Claude
Gemini
Qwen
Llama
```

Its basic role is:

```text
input → inference → output
```

### 2. Agent

Software around a model that repeatedly makes decisions and uses tools:

```text
goal
 ↓
reason
 ↓
act
 ↓
observe
 ↓
repeat
```

### 3. Workflow

A predefined process:

```text
A → B → C → D
```

or:

```text
A
├── B
├── C
└── D
```

### 4. Orchestrator

The thing managing:

```text
agents
tasks
dependencies
state
retries
timeouts
approvals
results
```

So for a project-oriented AI system:

```text
                 Orchestrator
                      │
                    Project
                      │
                ┌─────┴─────┐
                ▼           ▼
              Task 1      Task 2
                │           │
              Agent       Agent
                │           │
              Tools       Tools
                │           │
                └─────┬─────┘
                      ▼
                Project state
```

That is probably the direction you're ultimately interested in.

---

# What I would **not** teach you first

I wouldn't start you with:

```text
LangChain
LangGraph
CrewAI
AutoGen
Semantic Kernel
agent swarms
vector databases
complex RAG pipelines
multi-agent frameworks
```

Not because they're necessarily bad, but because frameworks can hide the concepts you actually need to understand.

If you first understand the underlying mechanics, later you'll look at something like LangGraph and immediately think:

> Ah, this is basically a state machine / graph around LLM calls and tools.

That's much better than learning the framework without understanding why it exists.

---

# Our practical curriculum

So I'd turn your learning into this progression:

```text
FOUNDATIONS

Stage 0  Mental model of AI engineering
Stage 1  LLM application fundamentals
Stage 2  Structured output

AGENT FUNDAMENTALS

Stage 3  Tool calling
Stage 4  Agent loop
Stage 5  Context, state and memory

KNOWLEDGE & ORCHESTRATION

Stage 6  RAG and external knowledge
Stage 7  Workflow orchestration
Stage 8  Project/task orchestration
Stage 9  Multi-agent systems

PRODUCTION ENGINEERING

Stage 10 Evaluation
Stage 11 Guardrails and human approval
Stage 12 Observability, cost and reliability
Stage 13 MCP and integration architecture
Stage 14 Production deployment
```

And throughout the learning process, we should **build one project progressively** rather than create unrelated toy examples.

A good learning project would be a CLI-based engineering agent:

```text
engineering-agent
│
├── asks an LLM questions
├── uses structured output
├── calls safe tools
├── investigates problems
├── remembers investigation state
├── breaks goals into tasks
├── tracks task dependencies
├── executes a workflow
├── reviews its own work
├── uses MCP tools
└── eventually connects safely to real infrastructure
```

That gives us a natural path from:

```text
print("Hello AI")
```

all the way to:

```text
"Investigate why this OpenStack VM failed."

          ↓

AI creates investigation plan

          ↓

Task 1 → inspect Nova
Task 2 → inspect Placement
Task 3 → inspect compute nodes
Task 4 → correlate logs

          ↓

Agent executes safe tools

          ↓

Reviewer validates evidence

          ↓

Final diagnosis + evidence
```

That is the sort of project that will teach you **AI engineering, agent engineering, workflow orchestration, task management, MCP, safety, and production architecture together**.

Given that you're starting from very little AI-specific knowledge, I'd treat **Stage 0 as a genuine lesson rather than a quick glossary**: model vs LLM vs agent, tokens, context windows, inference, prompts, tool calling, deterministic vs probabilistic software, and why AI programs need a different architecture from traditional programs. From there, we'd proceed stage by stage and build the engineering agent alongside the theory.
