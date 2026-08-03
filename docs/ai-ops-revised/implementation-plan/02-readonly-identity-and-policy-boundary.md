# 02. Read-Only Identity and Policy Boundary

## 02.1 Goal

Create dedicated credential profiles and empirically prove that the default assistant can read useful project state while create, update, and delete actions remain unauthorized.

Target outcome:

```text
dedicated identity -> protected project-reader profile -> read matrix passes -> mutation matrix fails -> broader scopes remain separate
```

## 02.2 Estimate

Total estimate:

```text
1.5-3 engineer-days
9-18 focused hours
```

## 02.3 Scope

Included:

* Select the initial project and expected project-reader visibility.
* Create a dedicated identity and preferably an application credential.
* Configure protected named cloud-profile material.
* Validate read behavior and representative mutation denial.
* Document policy/version differences, lifecycle, and future operator-reader separation.

Excluded:

* Using human admin or member credentials as the runtime default.
* Changing OpenStack policy merely to make a diagnostic pass.
* Enabling operator-reader tools.
* Creating restricted host SSH access.
* Implementing the diagnostic toolbox.

## 02.4 Assumptions

- [ ] A human administrator can create a fresh revised identity, role assignment, and application credential.
- [ ] No credential, application secret, cloud profile, token, or private key is copied from the prior AI-OPS runtime.
- [ ] Revised identity and profile names are distinct from the prior runtime so both boundaries can be revoked and audited independently.
- [ ] The selected project has representative servers, networks, ports, volumes, images, or security groups for read validation.
- [ ] Secure RBAC behavior varies by OpenStack release and must be measured rather than assumed.
- [ ] Project-reader remains the default even if a broader operator-reader profile is introduced later.

## 02.5 Ordered Tasks

### Step 1 - Define the Credential and Policy Matrix

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Select and document the initial project, domain, role, revised profile name, owner, purpose, expiry, and rotation expectation; confirm the name does not collide with the prior runtime.
- [ ] List the project-visible resource reads required by the MVP.
- [ ] List representative create, update, and delete operations that must be denied.
- [ ] List service, hypervisor, and Neutron-agent reads expected to require a separate operator-reader profile.
- [ ] Define blocking behavior: any unexpected mutation success stops rollout and triggers credential revocation.

Done when:

- [ ] The expected read and denial behavior is written before credentials are installed.

### Step 2 - Create Dedicated Project-Reader Access

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Create a fresh dedicated revised AI-OPS identity rather than reusing a human account or copying the prior runtime’s identity material.
- [ ] Assign only the least-privileged project reader role supported by the deployed policy.
- [ ] Prefer an application credential with the narrowest supported role and lifecycle.
- [ ] Record non-secret metadata and the administrator-controlled creation procedure.
- [ ] Keep operator-reader creation deferred unless the policy matrix proves it is necessary for a later phase.

Done when:

- [ ] A dedicated, revocable, non-admin credential exists for the selected project.

### Step 3 - Protect Runtime Credential Material

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Configure a distinctly named revised project-reader cloud profile in the revised runtime credential location; do not overwrite or reference the prior runtime’s profile path.
- [ ] Restrict credential directory and file permissions to the runtime identity that needs them.
- [ ] Ensure tokens, passwords, secrets, and private keys are absent from repository history, samples, process arguments, and logs.
- [ ] Add only a redacted profile example and documented environment contract to source control.
- [ ] Verify the profile is not inherited by unrelated operator or provisioning sessions.

Done when:

- [ ] CLI and SDK clients can locate the profile while secret material remains protected and uncommitted.

### Step 4 - Validate Required Reads

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Verify token issuance and project scope.
- [ ] Verify server, network, subnet, port, volume, image, and security-group reads required by the MVP.
- [ ] Record exact authorization or endpoint failures without broadening scope automatically.
- [ ] Distinguish policy limitations, empty project state, missing service catalogs, and connectivity failures.
- [ ] Save only redacted evidence of the tested operation and result class.

Done when:

- [ ] The project-reader can collect enough project state for the three initial diagnostics.

### Step 5 - Prove Mutation Denial

Estimate:

```text
0.5-0.75 engineer-days
3-4.5 hours
```

Tasks:

- [ ] Design safe denial tests that cannot damage existing resources if policy is misconfigured.
- [ ] Attempt representative create operations with unique disposable names and verify authorization denial before creation.
- [ ] Attempt representative update and delete operations against non-existent or controlled disposable targets and verify denial.
- [ ] Check afterward that no resource was created or changed.
- [ ] Revoke the credential and stop implementation immediately if any mutation succeeds.

Done when:

- [ ] Read access succeeds and representative create, update, and delete attempts are demonstrably blocked.

### Step 6 - Document Lifecycle and Broader-Scope Gate

Estimate:

```text
0.25-0.5 engineer-days
1.5-3 hours
```

Tasks:

- [ ] Publish the tested read/denial matrix without secrets.
- [ ] Document rotation, expiry, revocation, replacement, and local profile removal.
- [ ] Define when an operator-reader profile is justified and require explicit tool-to-profile mapping.
- [ ] Require missing broader credentials to produce an unavailable diagnostic rather than fallback to admin authority.
- [ ] Add a recurring credential-boundary validation procedure for upgrades or policy changes.

Done when:

- [ ] Future maintainers can reproduce the boundary and safely revoke all assistant authority.

## 02.6 Phase Definition of Done

This phase is done when:

- [ ] A fresh, distinctly named, protected revised project-reader profile authenticates successfully without using prior runtime credential material.
- [ ] Required project-resource reads pass or have explicit accepted limitations.
- [ ] Representative create, update, and delete operations fail authorization checks.
- [ ] No human admin, root, database, RabbitMQ, or unrestricted service credential is available to AI-OPS.
- [ ] Credential metadata, policy behavior, rotation, and revocation are documented.
- [ ] Operator-reader remains separate and unavailable by default.

## 02.7 Risks

| Risk | Mitigation |
| ---- | ---------- |
| Reader role permits unexpected mutation | Use safe negative tests and revoke immediately on any success. |
| Reader policy is too narrow across versions | Record the actual matrix and degrade tools to unavailable instead of escalating silently. |
| Credential leaks through examples or evidence | Commit only redacted contracts and scan evidence before retention. |
| Operator-reader becomes the convenient default | Require per-tool profile declarations and deny fallback between profiles. |
| Denial tests accidentally affect real state | Use unique disposable/non-existent targets and verify post-test state. |
