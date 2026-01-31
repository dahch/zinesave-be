
# Brand Colors
COLOR_PRIMARY = "#F59E0B"  # Orange/Gold
COLOR_TEXT_MAIN = "#1F2937"  # Dark Gray/Slate 800
COLOR_TEXT_MUTED = "#6B7280"  # Gray 500
COLOR_BG_BODY = "#F3F4F6"  # Gray 100
COLOR_BG_CARD = "#FFFFFF"
COLOR_BUTTON_TEXT = "#FFFFFF"

# Logo URL
# IMPORTANT: We use a linked image because embedding a large Base64 string ( > 102KB)
# causes Gmail to clip the message, breaking the HTML structure.
# Please ensure this URL is publicly accessible.
# You can replace this with f"{frontend_url}/logo.png" if you host it there.
LOGO_URL = "https://zinesave.io/icon.png" 

def get_base_styles():
    # We remove the block style for the most part and will inline everything.
    # However, we keep a small block for media queries which cannot be inlined.
    return f"""
    <style>
        /* Mobile styles */
        @media screen and (max-width: 600px) {{
            .content {{ padding: 24px !important; }}
            .header {{ padding: 20px !important; }}
            .logo-img {{ height: 28px !important; }}
            .logo-text {{ font-size: 20px !important; }}
            .button {{ padding: 12px 24px !important; width: 100% !important; box-sizing: border-box !important; text-align: center !important; }}
            .main-table {{ width: 100% !important; }}
            .wrapper {{ padding: 0 !important; }}
        }}
    </style>
    """

def create_verification_email(verification_link: str, frontend_url: str):
    """
    Creates the HTML content for the verification email.
    Uses inline CSS for maximum compatibility (Gmail, Outlook, etc.).
    """
    
    # Inline Styles
    style_body = f"margin: 0; padding: 0; width: 100%; background-color: {COLOR_BG_BODY}; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;"
    style_wrapper = f"width: 100%; background-color: {COLOR_BG_BODY}; padding: 40px 0;"
    style_table = f"margin: 0 auto; max-width: 600px; width: 100%; background-color: {COLOR_BG_CARD}; border-radius: 8px; overflow: hidden; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;"
    style_header = f"padding: 24px; text-align: center; background-color: #ffffff; border-bottom: 1px solid #f0f0f0;"
    style_content = f"padding: 32px 24px; color: {COLOR_TEXT_MAIN}; line-height: 1.6; font-size: 16px; background-color: #ffffff;"
    style_footer = f"padding: 24px; text-align: center; font-size: 12px; color: {COLOR_TEXT_MUTED}; background-color: {COLOR_BG_BODY}; font-family: sans-serif;"
    style_button = f"display: inline-block; background-color: {COLOR_PRIMARY}; color: {COLOR_BUTTON_TEXT}; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 16px;"
    style_h1 = f"margin-top: 0; color: {COLOR_TEXT_MAIN}; font-size: 24px; font-weight: bold;"
    style_p = f"margin-bottom: 16px; color: {COLOR_TEXT_MAIN};"
    style_link = f"color: {COLOR_PRIMARY}; word-break: break-all;"
    style_footer_link = f"color: {COLOR_TEXT_MUTED}; text-decoration: underline; margin: 0 8px;"
    style_logo_text = f"font-size: 24px; font-weight: bold; color: {COLOR_TEXT_MAIN}; vertical-align: middle; font-family: sans-serif;"
    style_logo_img = f"vertical-align: middle; height: 32px; width: auto; margin-right: 10px; border: 0;"

    # Header Content with Table for Alignment
    header_content = f"""
    <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="margin: 0 auto;">
        <tr>
            <td style="vertical-align: middle;">
                <img src="{LOGO_URL}" alt="ZineSave" class="logo-img" style="{style_logo_img}" width="32" height="32">
            </td>
            <td class="logo-text" style="{style_logo_text}">
                Zine<span style="color:{COLOR_PRIMARY}">Save</span>
            </td>
        </tr>
    </table>
    """
    
    return f"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Verify your email</title>
    {get_base_styles()}
</head>
<body style="{style_body}">
    <center style="width: 100%; background-color: {COLOR_BG_BODY};">
        <div class="wrapper" style="{style_wrapper}">
            <!--[if mso]>
            <table role="presentation" width="600" align="center" style="width:600px;">
            <tr>
            <td style="padding:0;">
            <![endif]-->
            <table class="main-table" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="{style_table}">
                <tr>
                    <td class="header" style="{style_header}">
                        {header_content}
                    </td>
                </tr>
                <tr>
                    <td class="content" style="{style_content}">
                        <h1 style="{style_h1}">Verify your email address</h1>
                        <p style="{style_p}">Welcome to ZineSave! We're excited to help you turn the web into ePub.</p>
                        <p style="{style_p}">Please confirm your account by clicking the button below:</p>
                        
                        <div class="button-wrapper" style="text-align: center; margin: 32px 0;">
                            <a href="{verification_link}" class="button" style="{style_button}">Verify Email</a>
                        </div>
                        
                        <p style="{style_p}; font-size: 14px; color: {COLOR_TEXT_MUTED}; margin-top: 24px;">
                            If the button doesn't work, copy and paste this link into your browser:<br>
                            <a href="{verification_link}" style="{style_link}">{verification_link}</a>
                        </p>
                        
                        <p style="{style_p}; margin-top: 32px; color: {COLOR_TEXT_MUTED};">
                            If you didn't create an account, you can safely ignore this email.
                        </p>
                    </td>
                </tr>
            </table>
            <!--[if mso]>
            </td>
            </tr>
            </table>
            <![endif]-->
            
            <div class="footer" style="{style_footer}">
                <p style="margin-bottom: 8px;">&copy; 2026 ZineSave. All rights reserved.</p>
                <p>
                    <a href="{frontend_url}/privacy" style="{style_footer_link}">Privacy Policy</a>
                    <a href="{frontend_url}/terms" style="{style_footer_link}">Terms of Service</a>
                </p>
            </div>
        </div>
    </center>
</body>
</html>
"""
