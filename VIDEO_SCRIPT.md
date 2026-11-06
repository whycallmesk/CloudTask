# CloudTask: 10-Minute Demo Video Script (3 speakers)

Record with any screen recorder (Zoom or Google Meet recording works). Every member must speak. Rehearse once; keep to ~10 minutes.
Replace [Name A/B/C] with your names. Suggested split: A = problem + architecture, B = services + implementation, C = live demo + conclusion.

| Time | Speaker | On screen | What to say |
|---|---|---|---|
| 0:00-0:45 | A | Title slide: project name, course, names | Introduce group and project: "CloudTask is a task manager deployed on AWS as a scalable, highly available three-tier application." |
| 0:45-1:45 | A | Slide: problem statement | One server means one point of failure, no elasticity, and an exposed database. We wanted automatic scaling, high availability and a private database. |
| 1:45-3:30 | A | Architecture diagram (from the report) | Walk the path: Users -> ALB -> EC2 instances in two zones -> RDS in private subnets; S3 for files. Mention security groups chain and the IAM role. |
| 3:30-5:00 | B | Slide or table of AWS services | One line per service: VPC, EC2, ALB, Auto Scaling, RDS, S3, IAM, Security Groups, SSM, CloudWatch, CloudFormation. |
| 5:00-6:30 | B | VS Code: `app.py`, then `template.yaml` | Show routes (`/`, `/health`, `/cpu`), then the template: ASG min 2 / max 4, target 50% CPU, RDS in private subnets, UserData bootstrap. Explain infrastructure as code. |
| 6:30-7:15 | B | AWS console: CloudFormation stack, Outputs tab | Show the stack in `CREATE_COMPLETE` (pre-deploy before recording; it takes ~15 min). Click AppURL. |
| 7:15-8:15 | C | Browser: the app | Add a task with an attachment, mark done, refresh several times and point at the changing instance name (load balancing). |
| 8:15-9:15 | C | EC2 console + CloudWatch dashboard | Terminate one instance -> replacement launches (self-healing). Start `./load_test.sh` and show CPU rising and instance count increasing (speed up or show a pre-recorded clip, scaling takes a few minutes). |
| 9:15-10:00 | C | Closing slide | Results: report the actual test outcomes observed during deployment; do not claim tests passed unless you ran them. Future work: Multi-AZ RDS, HTTPS, Cognito, CI/CD. Mention cleanup: stack deleted to avoid cost. Thank you. |

## Recording tips
- Deploy the stack **before** recording; start the load test ~5 minutes earlier so scaling is already visible.
- Keep AWS console tabs open: CloudFormation, EC2 instances, Auto Scaling group Activity, CloudWatch dashboard `CloudTask`.
- Blur or avoid showing your DB password and account ID.
- After the video, delete the stack (empty the S3 bucket first).
