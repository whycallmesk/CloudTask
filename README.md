# CloudTask — Scalable Web Application on AWS

A task-manager web app deployed on AWS using a classic scalable 3-tier architecture.
The whole infrastructure is created from one CloudFormation template (Infrastructure as Code).

## Architecture

```
Internet
   |
Application Load Balancer (public subnets, 2 AZs)
   |
Auto Scaling Group: 2-4 EC2 instances running Flask + Gunicorn (scales at 50% CPU)
   |                          \
Amazon RDS MySQL              Amazon S3 (file attachments, private bucket)
(private subnets)
```

Also used: VPC, Security Groups, IAM role, CloudWatch dashboard and alarm.

## AWS services used
| Service | Purpose |
|---|---|
| VPC, subnets, IGW, route tables | Network isolation (public tier + private DB tier) |
| EC2 + Launch Template | App servers (Amazon Linux 2023, bootstrapped by UserData) |
| Application Load Balancer | Distributes traffic, health checks `/health` |
| Auto Scaling Group | Self-healing and CPU-based scale out/in (2-4 instances) |
| RDS MySQL 8.0 | Managed relational database in private subnets |
| S3 | Stores task attachments (private, presigned download links) |
| IAM | Instance role with least-privilege S3 access |
| Security Groups | ALB -> app (8000) -> DB (3306) chain only |
| CloudWatch | Dashboard (CPU, requests, instances, RDS) + unhealthy-host alarm |
| CloudFormation | Provisions everything from `infra/template.yaml` |

## Project structure
```
cloudtask/
  app/app.py               Flask application
  app/templates/index.html UI
  app/requirements.txt
  infra/template.yaml      CloudFormation template
  load_test.sh             generates load to demo auto scaling
```

## Deploy (about 15 minutes)

1. **Push this folder to a public GitHub repo** (the instances clone it at boot).
   ```bash
   git init && git add . && git commit -m "CloudTask"
   git branch -M main
   git remote add origin https://github.com/<your-user>/cloudtask.git
   git push -u origin main
   ```
2. Sign in to the **AWS Console** in the region shown at the top-right. For your current setup, keep `ap-southeast-2` (Sydney) selected. Open **CloudFormation -> Create stack -> With new resources**.
3. Upload `infra/template.yaml`.
4. Fill parameters:
   - `RepoUrl`: `https://github.com/<your-user>/cloudtask.git`
   - `DBPassword`: use a new, unique password containing letters and digits only, 8+ characters. Do not reuse your email or other account password.
5. Tick the acknowledgement for IAM resources if shown, then **Create stack**.
6. Wait until the status is `CREATE_COMPLETE` (RDS takes ~10 min).
7. Open the **Outputs** tab and click **AppURL**.

## Try it
- Add tasks, upload an attachment, mark done, delete. Data is stored in RDS, files in S3.
- Refresh several times: the *Served by instance* badge changes, showing load balancing.
- **Self-healing:** EC2 console -> terminate one instance; the ASG launches a replacement.
- **Auto scaling:** from your laptop run
  ```bash
  chmod +x load_test.sh
  ./load_test.sh http://<AppURL-host> 30 600
  ```
  Watch CloudWatch dashboard **CloudTask** and EC2 -> Auto Scaling Groups -> Activity; instances rise from 2 toward 4.

## Clean up (important, to avoid charges)
1. S3 console: empty the attachments bucket (name is in stack Outputs).
2. CloudFormation: delete the stack.

## Cost note
This stack creates billable resources: an Application Load Balancer, two or more EC2 instances, an RDS database, storage, and monitoring. These costs consume your available AWS credits. The exact amount depends on region, runtime, traffic, and data transfer. Keep the stack running only while you are actively testing/recording, check **Cost and usage**, and delete it immediately afterward. Do not upgrade the account plan just to deploy this project.

## Local run (optional, for development)
```bash
cd app
pip install -r requirements.txt
export DB_HOST=localhost DB_USER=root DB_PASSWORD=secret DB_NAME=cloudtask
python app.py        # needs a local MySQL with database "cloudtask"
```

## Troubleshooting
- Targets unhealthy for the first ~5 minutes is normal while instances bootstrap.
- Check logs: EC2 -> instance -> Connect -> Session Manager -> `sudo journalctl -u cloudtask` and `/var/log/cloud-init-output.log`.
- Stack fails on RDS version: change `EngineVersion` to a version available in your region.
