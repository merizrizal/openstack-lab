# 02. Read-Only Credential Boundary

## 02.1 Goal

Create dedicated OpenStack diagnostic credentials and prove the assistant can observe project state while mutation remains blocked.

Target outcome:

```text
dedicated identity -> project-reader profile configured -> read checks pass -> mutation checks fail -> credential behavior documented
```

## 02.2 Estimate

Total estimate:

```text
1.5-3 engineer-days
9-18 focused hours
```

## 02.3 Scope

Included:

* Create or request a dedicated OpenStack identity for AI-OPS diagnostics.
* Configure a project-scoped reader credential profile.
* Protect credential files on the assistant runtime.
* Run read and mutation validation checks.
* Document actual policy behavior.
* Decide whether an operator-reader profile is needed later.

Excluded:

* Implementing operator-reader diagnostics.
* Implementing SSH observer access.
* Adding diagnostic scripts beyond credential validation commands.
* Changing OpenStack policy files unless validation proves current policy cannot support the MVP.

## 02.4 Assumptions

- [ ] Keystone is reachable from the assistant runtime.
- [ ] A human admin can create the initial AI-OPS identity and role assignment.
- [ ] The initial diagnostic project contains or can see representative lab resources.
- [ ] OpenStack reader behavior must be tested because policy enforcement can vary.

## 02.5 Ordered Tasks

### Step 1 - Choose Initial Credential Scope

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Select the initial OpenStack project that the AI-OPS project-reader credential should inspect.
- [ ] Record why this project is appropriate for the first MVP diagnostics.
- [ ] Identify which commands are expected to work with project-reader scope.
- [ ] Identify which operator-level commands are expected to fail or be deferred.

Done when:

- [ ] The first credential scope is explicit enough to configure and test.

### Step 2 - Create Dedicated Read-Only Identity

Estimate:

```text
0.5-1 engineer-days
3-6 hours
```

Tasks:

- [ ] Create or request a dedicated AI-OPS read-only OpenStack user.
- [ ] Assign the least-privileged reader role available for the selected project.
- [ ] Prefer an application credential when Keystone supports it.
- [ ] Avoid using any human admin credential, admin-openrc, or member-role credential as the assistant default.
- [ ] Record the non-secret metadata: credential purpose, scope, role, owner, creation date, and rotation expectation.

Done when:

- [ ] A dedicated non-admin diagnostic identity exists and is ready to configure on the assistant runtime.

### Step 3 - Configure Protected Cloud Profile

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Configure a named project-reader cloud profile on the assistant runtime.
- [ ] Store credential material only in the designated credential area.
- [ ] Set restrictive directory and file permissions.
- [ ] Verify credential files are not committed to the repository.
- [ ] Add a redacted example profile for documentation if useful.

Done when:

- [ ] OpenStack CLI and SDK can locate the profile, and the real secret material remains local and protected.

### Step 4 - Validate Read Access

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Verify token issuance succeeds with the project-reader profile.
- [ ] Verify listing project-visible servers succeeds.
- [ ] Verify listing project-visible networks, subnets, ports, volumes, images, and security groups succeeds where policy allows.
- [ ] Record any read command that unexpectedly fails.
- [ ] Distinguish expected policy limitation from configuration error.

Done when:

- [ ] The assistant can inspect enough project-level resources to support the first diagnostic toolbox.

### Step 5 - Validate Mutation Denial

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Attempt representative create operations using harmless test names and confirm they fail before resource creation.
- [ ] Attempt representative update operations only where they are safe to test and confirm they fail.
- [ ] Attempt representative delete operations only against non-existent or safe test targets and confirm authorization denial.
- [ ] Record exact failure class such as forbidden, not authorized, or policy denial.
- [ ] Treat any successful mutation as a blocking safety failure.

Done when:

- [ ] Mutation is empirically blocked for the default AI-OPS credential.

### Step 6 - Document Actual Credential Matrix

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Document which read commands pass.
- [ ] Document which mutation commands fail.
- [ ] Document which operator visibility commands fail or require later operator-reader scope.
- [ ] Add a rotation/revocation note for the credential.
- [ ] Add rollback instructions to revoke the credential and remove local profile material.

Done when:

- [ ] Future tool authors can tell which credential should be used for project-level diagnostics and which capabilities remain deferred.

## 02.6 Phase Definition of Done

This phase is done when:

- [ ] A dedicated project-reader credential is configured on the assistant runtime.
- [ ] The credential can authenticate and inspect project-visible resources.
- [ ] Representative mutation attempts fail.
- [ ] Credential files are protected and not committed.
- [ ] Actual reader-role behavior is documented.
- [ ] Operator-reader needs are identified but not mixed into the default profile.

## 02.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Reader role behaves differently than expected | Use an explicit read/mutation validation matrix and treat unexpected mutation as blocking. |
| Credential material leaks into git | Keep real profiles outside committed docs and include only redacted examples. |
| Project-reader scope is too narrow for useful diagnostics | Start with server/network/volume/image tools; defer operator health to separate profile. |
| Operator-reader profile becomes the default | Keep project-reader as default and require explicit tool classification for broader scope. |