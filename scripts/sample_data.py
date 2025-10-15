"""
Sample test data for testing AI integration.

Provides realistic resume text and job descriptions for manual and automated testing.
"""

# Sample resume - Software Engineer
SAMPLE_RESUME_TEXT = """
Sarah Johnson
Senior Software Engineer
Email: sarah.johnson@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/sarahjohnson | GitHub: github.com/sarahjohnson

PROFESSIONAL SUMMARY
Software engineer with 6 years of experience building scalable web applications.
Proficient in Python, JavaScript, and cloud technologies.

WORK EXPERIENCE

Software Engineer | Tech Solutions Inc | San Francisco, CA | 2021 - Present
• Developed backend APIs using Python and FastAPI
• Worked with Docker containers for application deployment
• Managed PostgreSQL databases
• Collaborated with team of 5 developers
• Implemented new features based on customer feedback

Junior Developer | StartupCo | Remote | 2018 - 2021
• Built web applications using JavaScript
• Worked on frontend and backend development
• Used Git for version control
• Participated in daily standup meetings

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley | 2014 - 2018
GPA: 3.7/4.0

SKILLS
Languages: Python, JavaScript, SQL
Frameworks: FastAPI, React
Tools: Docker, Git
Databases: PostgreSQL, MongoDB
"""

# Sample job descriptions for different scenarios

JOB_SENIOR_PYTHON = """
We are seeking a Senior Python Developer to join our engineering team.

Requirements:
• 5+ years of professional software development experience
• Expert knowledge of Python and FastAPI framework
• Strong experience with Docker and containerization
• Experience with PostgreSQL and database optimization
• Proficiency with AWS cloud services (EC2, S3, Lambda, RDS)
• Experience with Kubernetes for container orchestration
• Knowledge of CI/CD pipelines and DevOps practices
• Strong understanding of RESTful API design
• Experience with microservices architecture
• Excellent problem-solving and communication skills

Nice to Have:
• Experience with Redis for caching
• Knowledge of GraphQL
• Contributions to open-source projects
• Experience with event-driven architecture

About the Role:
You will be responsible for designing and implementing scalable backend services,
optimizing database performance, and mentoring junior developers. This is a
full-time position with competitive salary and benefits.
"""

JOB_FULLSTACK_DEVELOPER = """
Full Stack Developer needed for fast-growing startup.

Must Have:
• 3+ years of full stack development experience
• Strong Python backend skills (FastAPI, Django, or Flask)
• Frontend experience with React or Vue.js
• Experience with Docker and containerization
• PostgreSQL or MySQL database experience
• Understanding of RESTful API design
• Experience with Git and version control
• Excellent communication skills for remote team

Responsibilities:
• Build and maintain web applications
• Develop RESTful APIs for frontend consumption
• Write clean, maintainable, and well-tested code
• Collaborate with designers and product managers
• Participate in code reviews and technical discussions
• Deploy applications to cloud platforms (AWS or GCP)

We Offer:
• Competitive salary
• Remote-first culture
• Flexible working hours
• Health benefits
• Professional development budget
"""

JOB_BACKEND_ENGINEER = """
Backend Engineer - Python/FastAPI

We're looking for a talented Backend Engineer to help build our platform.

Technical Requirements:
• Strong Python programming skills
• Experience with FastAPI or similar async frameworks
• PostgreSQL database experience
• Docker and containerization
• Understanding of microservices architecture
• AWS experience (EC2, RDS, S3, Lambda)
• Experience with message queues (RabbitMQ, SQS, or Kafka)
• Knowledge of caching strategies (Redis, Memcached)
• Experience writing unit and integration tests
• CI/CD experience with GitHub Actions or similar

Soft Skills:
• Excellent problem-solving abilities
• Strong communication skills
• Ability to work independently and in teams
• Passion for learning new technologies
• Attention to detail

Location: Remote (US timezone preferred)
Salary: $120k - $160k based on experience
"""

JOB_DEVOPS_ENGINEER = """
DevOps Engineer - Cloud Infrastructure

Join our DevOps team to build and maintain our cloud infrastructure.

Required Skills:
• 4+ years of DevOps/SRE experience
• Strong Python scripting skills
• Expert knowledge of AWS services (EC2, ECS, Lambda, RDS, S3, CloudFormation)
• Kubernetes experience for container orchestration
• Docker containerization
• Infrastructure as Code (Terraform or CloudFormation)
• CI/CD pipeline setup (Jenkins, GitLab CI, or GitHub Actions)
• Monitoring and logging (Prometheus, Grafana, ELK stack)
• Experience with configuration management (Ansible, Chef, or Puppet)

Responsibilities:
• Design and implement scalable cloud infrastructure
• Automate deployment processes
• Monitor system performance and reliability
• Implement security best practices
• Troubleshoot production issues
• Collaborate with development teams
• Document infrastructure and processes

This is a critical role in our growing engineering organization.
Competitive salary, benefits, and remote work options available.
"""

# Sample responses for testing
SAMPLE_API_RESPONSE = {
    "match_score": 52.4,
    "ats_score": 78,
    "semantic_similarity": 35,
    "matching_keywords": ["python", "fastapi", "docker", "postgresql", "experience"],
    "missing_keywords": ["aws", "kubernetes", "ci/cd", "microservices", "cloud"],
    "ats_issues": [
        {
            "type": "missing_section",
            "severity": "high",
            "section": "Experience",
            "message": "Experience section lacks quantifiable achievements",
            "recommendation": "Add specific metrics (e.g., 'Improved API performance by 40%')",
        }
    ],
}
