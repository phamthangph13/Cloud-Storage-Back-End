from flask import current_app, render_template_string
from flask_mail import Message
from Authenticator import mail
import jwt
from datetime import datetime, timedelta

def generate_verification_token(user_id):
    """Generate a verification token for email confirmation"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
        'type': 'email_verification'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def generate_reset_token(user_id):
    """Generate a token for password reset"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'type': 'password_reset'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token, token_type):
    """Verify a token and return the user_id if valid"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if payload['type'] != token_type:
            return None
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def send_verification_email(user_email, token):
    """Send verification email to user"""
    verification_url = f"http://localhost:5000/api/auth/verify-email-link?token={token}"
    
    html_template = """
    <!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xác Thực Email</title>
    <style>
        body {
            font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .header {
            background-color: #4285F4;
            color: white;
            padding: 20px 30px;
            text-align: center;
        }
        .header h2 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }
        .content {
            padding: 30px;
        }
        .verify-button {
            display: block;
            background-color: #34A853;
            color: white;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 4px;
            font-weight: bold;
            margin: 25px auto;
            text-align: center;
            width: 200px;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        .verify-button:hover {
            background-color: #2E8B47;
        }
        .warning-box {
            background-color: #FEEFE3;
            border-left: 4px solid #EA4335;
            padding: 16px;
            margin: 20px 0;
            font-weight: 500;
        }
        .warning-icon {
            color: #EA4335;
            font-weight: bold;
            margin-right: 8px;
        }
        .link-container {
            background-color: #F1F3F4;
            padding: 15px;
            border-radius: 4px;
            word-break: break-all;
            margin: 20px 0;
            font-size: 14px;
            font-family: monospace;
        }
        .footer {
            background-color: #F8F9FA;
            padding: 20px 30px;
            text-align: center;
            font-size: 14px;
            color: #5F6368;
            border-top: 1px solid #DADCE0;
        }
        .logo {
            margin-bottom: 15px;
            width: 120px;
            height: auto;
        }
        .divider {
            border-top: 1px solid #DADCE0;
            margin: 20px 0;
        }
        .info-box {
            background-color: #E8F0FE;
            border-left: 4px solid #4285F4;
            padding: 16px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <!-- <img src="your-logo.png" alt="Logo Công Ty" class="logo"> -->
            <h2>XÁC THỰC TÀI KHOẢN EMAIL</h2>
        </div>
        
        <div class="content">
            <p>Xin chào Quý khách,</p>
            
            <p>Cảm ơn Quý khách đã đăng ký sử dụng dịch vụ của chúng tôi. Để hoàn tất quá trình đăng ký và kích hoạt tài khoản, vui lòng nhấp vào nút bên dưới:</p>
            
            <a href="{{verification_url}}" class="verify-button">XÁC THỰC EMAIL</a>
            
            <div class="warning-box">
                <span class="warning-icon">⚠️</span><strong>CẢNH BÁO QUAN TRỌNG:</strong> Nếu Quý khách không thực hiện việc đăng ký tài khoản với chúng tôi, vui lòng <strong>KHÔNG NHẤP</strong> vào nút xác thực và bỏ qua email này. Đây có thể là dấu hiệu của việc có người đang cố gắng sử dụng email của Quý khách trái phép.
            </div>
            
            <p>Nếu nút xác thực ở trên không hoạt động, Quý khách có thể sao chép và dán đường dẫn sau vào trình duyệt:</p>
            
            <div class="link-container">
                {{verification_url}}
            </div>
            
            <div class="info-box">
                <p><strong>Lưu ý:</strong></p>
                <ul>
                    <li>Đường dẫn xác thực này sẽ hết hạn sau 24 giờ vì lý do bảo mật.</li>
                    <li>Nếu Quý khách cần hỗ trợ, vui lòng liên hệ với bộ phận Chăm sóc Khách hàng của chúng tôi qua email: hotro@congty.com hoặc số điện thoại: 1900-xxxx.</li>
                </ul>
            </div>
            
            <p>Sau khi xác thực thành công, Quý khách sẽ có thể truy cập đầy đủ các tính năng của nền tảng chúng tôi.</p>
            
            <div class="divider"></div>
            
            <p>Trân trọng,<br><strong>Đội ngũ Công ty XYZ</strong></p>
        </div>
        
        <div class="footer">
            <p>Đây là email tự động, vui lòng không trả lời email này.</p>
            <p>© 2025 Công ty XYZ. Tất cả các quyền được bảo lưu.</p>
            <p>Địa chỉ: 123 Đường ABC, Quận XYZ, TP. Hồ Chí Minh</p>
        </div>
    </div>
</body>
</html>
    """
    
    html_content = render_template_string(html_template, verification_url=verification_url)
    
    msg = Message(
        subject="Verify Your Email",
        recipients=[user_email],
        html=html_content
    )
    
    mail.send(msg)

def send_password_reset_email(user_email, token):
    """Send password reset email to user"""
    reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
    
    html_template = """
    <html>
    <body>
        <h2>Password Reset</h2>
        <p>You requested a password reset. Please click the link below to reset your password:</p>
        <p><a href="{{ reset_url }}">Reset Password</a></p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>This link will expire in 1 hour.</p>
    </body>
    </html>
    """
    
    html_content = render_template_string(html_template, reset_url=reset_url)
    
    msg = Message(
        subject="Password Reset Request",
        recipients=[user_email],
        html=html_content
    )
    
    mail.send(msg)