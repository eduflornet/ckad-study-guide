# CKAD Mock Exam Practice

## 📋 Mock Exam Format

Each mock exam contains 15-20 realistic CKAD questions with:
- **Time limit**: 2 hours (120 minutes)
- **Passing score**: 66% (at least 10-13 correct answers)
- **Environment**: Single Kubernetes cluster
- **Tools**: kubectl, vim/nano, bash

## 🎯 Available Mock Exams

### Practice Level (60-90 minutes)
- [**Mock Exam 1**](mock-exam-01.md) - Foundation concepts and basic tasks
- [**Mock Exam 2**](mock-exam-02.md) - Intermediate scenarios and configurations
- [**Mock Exam 3**](mock-exam-03.md) - Advanced networking and security

### Exam Level (120 minutes)
- [**Mock Exam 4**](mock-exam-04.md) - Full exam simulation with mixed difficulty
- [**Mock Exam 5**](mock-exam-05.md) - Complex multi-component scenarios
- [**Mock Exam 6**](mock-exam-06.md) - Final preparation with exam-level complexity

## 📊 Domain Distribution

Each mock exam follows the official CKAD domain weights:

| Domain | Questions | Percentage |
|--------|-----------|------------|
| Application Design and Build | 3-4 | 20% |
| Application Deployment | 3-4 | 20% |
| Application Observability | 2-3 | 15% |
| Environment & Security | 4-5 | 25% |
| Services and Networking | 3-4 | 20% |

## ⏱️ Time Management Strategy

### Question Analysis (1-2 minutes per question)
1. **Read carefully** - Understand all requirements
2. **Identify domain** - Know which concepts to apply
3. **Estimate complexity** - Simple (5-8 min), Medium (8-12 min), Complex (12-20 min)
4. **Plan approach** - kubectl commands, YAML files needed

### Execution Strategy
- **Start with easy questions** - Build confidence and momentum
- **Use generators** - `kubectl create` with `--dry-run=client -o yaml`
- **Test frequently** - Verify each step works
- **Skip if stuck** - Mark and return later
- **Save time for review** - 15-20 minutes at the end

## 🔧 Essential Setup Commands

Before starting any mock exam, run these setup commands:

```bash
# Set up kubectl alias and completion
alias k=kubectl
complete -F __start_kubectl k

# Set default namespace context
kubectl config set-context --current --namespace=default

# Quick environment check
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

## 📝 Scoring Guidelines

### Perfect Answer (100%)
- All requirements met exactly
- Resource is functional and accessible
- Follows best practices
- No syntax errors

### Good Answer (75-90%)
- Most requirements met
- Minor configuration issues
- Resource mostly functional
- Small syntax errors that don't break functionality

### Partial Answer (50-75%)
- Some requirements met
- Resource created but not fully functional
- Missing key configurations
- Syntax errors affecting functionality

### Poor Answer (0-50%)
- Few or no requirements met
- Resource not created or completely broken
- Major misunderstanding of requirements

## 🎯 Common Pitfalls to Avoid

1. **Not reading requirements carefully** - Missing key details
2. **Incorrect namespace** - Creating resources in wrong namespace
3. **Wrong selectors** - Labels don't match selectors
4. **Resource names** - Using incorrect names or formats
5. **Port configurations** - Wrong container ports or service ports
6. **YAML indentation** - Syntax errors breaking deployment
7. **Not testing** - Not verifying the solution works
8. **Time management** - Spending too much time on difficult questions

## 📚 Review and Analysis

After each mock exam:

1. **Check solutions** - Compare with provided answers
2. **Analyze mistakes** - Understand why answers were wrong
3. **Practice weak areas** - Focus on domains with low scores
4. **Time analysis** - Identify questions that took too long
5. **Retry difficult questions** - Practice until comfortable

## 🚀 Success Tips

- **Practice kubectl daily** - Build muscle memory for common commands
- **Use YAML generators** - Don't write YAML from scratch
- **Learn keyboard shortcuts** - vi/vim navigation and editing
- **Memorize port numbers** - Common application ports (80, 443, 3000, 8080)
- **Understand defaults** - Know what values are assumed when not specified
- **Practice under pressure** - Simulate exam time constraints

---

*Remember: The goal is not just to pass, but to become proficient with Kubernetes application development!*