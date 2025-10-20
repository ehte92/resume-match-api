"""
Seed script to populate database with system cover letter templates.
Run this manually after migrations: python -m app.scripts.seed_templates
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.models.cover_letter_template import CoverLetterTemplate


SYSTEM_TEMPLATES = [
    {
        "name": "Software Engineering - Professional",
        "description": "Clean, professional template for software engineering roles focusing on technical expertise and problem-solving",
        "category": "Software Engineering",
        "tone": "professional",
        "length": "medium",
        "template_text": """Dear Hiring Manager at {{company_name}},

I am writing to express my strong interest in the {{job_title}} position. With my background in software development and proven track record of delivering scalable solutions, I am confident I would be a valuable addition to your team.

My experience includes:
• Designing and implementing robust software systems
• Collaborating with cross-functional teams to deliver products on time
• Writing clean, maintainable code following best practices
• Continuously learning new technologies and methodologies

I am particularly drawn to {{company_name}} because of your commitment to innovation and technical excellence. I am excited about the opportunity to contribute to your projects and grow alongside your talented engineering team.

Thank you for considering my application. I look forward to discussing how my skills and experience align with your team's needs.

Best regards,
{{candidate_name}}""",
    },
    {
        "name": "Software Engineering - Enthusiastic",
        "description": "Energetic template for software engineering roles showcasing passion for technology and innovation",
        "category": "Software Engineering",
        "tone": "enthusiastic",
        "length": "medium",
        "template_text": """Dear Hiring Team at {{company_name}},

I'm thrilled to apply for the {{job_title}} position! Your company's innovative approach to solving complex technical challenges resonates deeply with my passion for creating impactful software solutions.

Throughout my career, I've been driven by the excitement of building products that make a difference. I absolutely love diving into challenging problems and emerging with elegant, scalable solutions. My experience includes working with modern tech stacks, contributing to open-source projects, and staying on the cutting edge of software development trends.

What really excites me about {{company_name}} is your commitment to pushing boundaries and your reputation for fostering a collaborative, growth-oriented engineering culture. I'm eager to bring my technical skills, creative problem-solving approach, and genuine enthusiasm to your team!

I would be absolutely delighted to discuss how I can contribute to your amazing projects. Thank you so much for this opportunity!

Warmly,
{{candidate_name}}""",
    },
    {
        "name": "Data Science - Professional",
        "description": "Analytics-focused template emphasizing data-driven insights and statistical expertise",
        "category": "Data Science",
        "tone": "professional",
        "length": "medium",
        "template_text": """Dear Hiring Manager at {{company_name}},

I am writing to apply for the {{job_title}} position. As a data scientist with expertise in statistical analysis, machine learning, and data visualization, I am excited about the opportunity to leverage data for strategic decision-making at {{company_name}}.

My experience encompasses:
• Developing predictive models and machine learning pipelines
• Extracting actionable insights from complex datasets
• Communicating findings effectively to both technical and non-technical stakeholders
• Collaborating with engineering teams to deploy models into production

I am impressed by {{company_name}}'s data-driven approach and commitment to using analytics to drive business outcomes. I believe my analytical mindset and technical skills would complement your team well.

Thank you for considering my application. I look forward to discussing how I can contribute to your data science initiatives.

Sincerely,
{{candidate_name}}""",
    },
    {
        "name": "Marketing - Enthusiastic",
        "description": "Creative and engaging template for marketing positions highlighting brand strategy and campaign success",
        "category": "Marketing",
        "tone": "enthusiastic",
        "length": "medium",
        "template_text": """Dear {{company_name}} Team,

I'm excited to apply for the {{job_title}} position! Your innovative campaigns and authentic brand voice have caught my attention, and I'm thrilled at the prospect of contributing my creative energy and marketing expertise to your team.

My background includes developing compelling brand narratives, executing multi-channel campaigns, and analyzing metrics to continuously optimize performance. I love crafting stories that resonate with audiences and drive meaningful engagement.

What draws me to {{company_name}} is your fresh approach to marketing and your commitment to creating genuine connections with your audience. I'm eager to bring my creativity, strategic thinking, and passion for storytelling to help amplify your brand's impact!

Let's chat about how I can help take your marketing efforts to the next level. Thank you for considering my application!

Best wishes,
{{candidate_name}}""",
    },
    {
        "name": "Product Management - Balanced",
        "description": "Well-rounded template for product management roles balancing vision, execution, and user empathy",
        "category": "Product Management",
        "tone": "balanced",
        "length": "medium",
        "template_text": """Dear {{company_name}} Hiring Team,

I am excited to apply for the {{job_title}} position. As a product manager who thrives at the intersection of technology, business, and user experience, I am drawn to {{company_name}}'s approach to building products that truly matter to users.

My product management experience includes:
• Defining product vision and strategy aligned with business goals
• Leading cross-functional teams through the product development lifecycle
• Conducting user research and translating insights into product requirements
• Making data-informed decisions to prioritize features and roadmap items

I appreciate {{company_name}}'s commitment to user-centric product development and your track record of delivering innovative solutions. I'm enthusiastic about the opportunity to contribute to your product strategy while learning from your talented team.

Thank you for considering my application. I look forward to discussing how my product management experience aligns with your needs.

Best regards,
{{candidate_name}}""",
    },
    {
        "name": "Design - Professional",
        "description": "Portfolio-focused template for design positions emphasizing user experience and creative process",
        "category": "Design",
        "tone": "professional",
        "length": "medium",
        "template_text": """Dear {{company_name}} Design Team,

I am writing to express my interest in the {{job_title}} position. As a designer passionate about creating intuitive, visually compelling user experiences, I am excited about the opportunity to contribute to {{company_name}}'s design excellence.

My design practice encompasses:
• User research and usability testing to inform design decisions
• Creating wireframes, prototypes, and high-fidelity mockups
• Collaborating closely with product and engineering teams
• Maintaining design systems and ensuring brand consistency

I admire {{company_name}}'s design philosophy and attention to detail in creating products that delight users. I would welcome the opportunity to bring my design thinking, technical skills, and collaborative approach to your team.

Thank you for considering my application. I look forward to sharing my portfolio and discussing how I can contribute to your design initiatives.

Sincerely,
{{candidate_name}}""",
    },
    {
        "name": "Sales - Enthusiastic",
        "description": "Results-driven template for sales roles highlighting relationship building and revenue achievements",
        "category": "Sales",
        "tone": "enthusiastic",
        "length": "short",
        "template_text": """Dear {{company_name}} Sales Team,

I'm thrilled to apply for the {{job_title}} position! Your company's growth trajectory and innovative sales approach have caught my attention, and I'm excited about the opportunity to contribute to your continued success.

I bring a proven track record of exceeding quotas, building lasting client relationships, and identifying new business opportunities. I love the thrill of closing deals and the satisfaction of helping clients solve their challenges with the right solutions.

{{company_name}}'s commitment to customer success aligns perfectly with my consultative sales philosophy. I'm eager to bring my energy, relationship-building skills, and competitive drive to help accelerate your revenue growth!

Let's discuss how I can contribute to your sales goals. Thank you for this exciting opportunity!

Best,
{{candidate_name}}""",
    },
    {
        "name": "Customer Success - Balanced",
        "description": "Empathetic template for customer success roles emphasizing client relationships and problem-solving",
        "category": "Customer Success",
        "tone": "balanced",
        "length": "medium",
        "template_text": """Dear {{company_name}} Team,

I am interested in the {{job_title}} position and excited about the opportunity to help your customers achieve their goals. With my background in customer success and genuine passion for building relationships, I believe I would be a strong fit for your team.

My customer success experience includes:
• Onboarding new clients and ensuring smooth product adoption
• Serving as a trusted advisor to help customers maximize value
• Identifying opportunities for account growth and expansion
• Collaborating with product teams to advocate for customer needs

I appreciate {{company_name}}'s customer-centric culture and commitment to delivering exceptional experiences. I'm enthusiastic about contributing to your customers' success while supporting your company's growth objectives.

Thank you for considering my application. I look forward to discussing how I can help strengthen your customer relationships.

Kind regards,
{{candidate_name}}""",
    },
]


def seed_templates():
    """Create system templates in the database."""
    db = SessionLocal()
    try:
        # Check if templates already exist
        existing = (
            db.query(CoverLetterTemplate).filter(CoverLetterTemplate.is_system == True).count()
        )

        if existing > 0:
            print(f"Found {existing} existing system templates. Skipping seed...")
            print("To re-seed, manually delete system templates first.")
            return

        # Create system templates
        created_count = 0
        for template_data in SYSTEM_TEMPLATES:
            template = CoverLetterTemplate(
                **template_data,
                is_system=True,
                user_id=None,  # System templates have no owner
                usage_count=0,
            )
            db.add(template)
            created_count += 1

        db.commit()
        print(f"✅ Successfully created {created_count} system templates!")
        print("\nCategories created:")
        categories = set(t["category"] for t in SYSTEM_TEMPLATES)
        for cat in sorted(categories):
            count = len([t for t in SYSTEM_TEMPLATES if t["category"] == cat])
            print(f"  - {cat}: {count} templates")

    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding cover letter templates...")
    seed_templates()
    print("\nDone!")
