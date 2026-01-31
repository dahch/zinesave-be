
from app.services.email_templates import create_verification_email

def test_template():
    link = "http://localhost:3000/verify?token=123"
    frontend = "http://localhost:3000"
    html = create_verification_email(link, frontend)
    
    output_file = "test_email.html"
    with open(output_file, "w") as f:
        f.write(html)
    
    print(f"Generated {output_file}")
    
    # Simple assertion to check if key elements are present
    assert "Zine" in html
    assert "Verify Email" in html
    assert "#F59E0B" in html # Check for primary color
    print("Template verification passed!")

if __name__ == "__main__":
    test_template()
