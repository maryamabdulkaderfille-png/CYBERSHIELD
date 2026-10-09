import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app(os.environ.get("FLASK_ENV", "development"))

try:
    with app.app_context():
        from app.extensions import bcrypt, db
        from app.models.user import User, UserRole
        db.create_all()

        # 1. Admin Account: maryamabdulkaderfille@gmail.com
        admin_email = "maryamabdulkaderfille@gmail.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        admin_hash = bcrypt.generate_password_hash("Admin12345!").decode("utf-8")
        if admin_user:
            admin_user.role = UserRole.ADMIN
            admin_user.is_verified = True
            admin_user.is_active = True
            admin_user.password_hash = admin_hash
            admin_user.failed_login_attempts = 0
            admin_user.locked_until = None
            db.session.commit()
            app.logger.info("Admin %s updated.", admin_email)
        else:
            admin_user = User(
                email=admin_email,
                username="maryam_admin",
                full_name="Maryam Abdulkader (Admin)",
                role=UserRole.ADMIN,
                is_verified=True,
                is_active=True,
                password_hash=admin_hash,
            )
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info("Admin %s created.", admin_email)

        # 2. Regular User Account: maryamabduqadir311@gmail.com
        reg_email = "maryamabduqadir311@gmail.com"
        reg_user = User.query.filter_by(email=reg_email).first()
        user_hash = bcrypt.generate_password_hash("User12345!").decode("utf-8")
        if reg_user:
            reg_user.role = UserRole.USER
            reg_user.is_verified = True
            reg_user.is_active = True
            reg_user.password_hash = user_hash
            reg_user.failed_login_attempts = 0
            reg_user.locked_until = None
            db.session.commit()
            app.logger.info("User %s updated.", reg_email)
        else:
            reg_user = User(
                email=reg_email,
                username="maryam_user",
                full_name="Maryam User",
                role=UserRole.USER,
                is_verified=True,
                is_active=True,
                password_hash=user_hash,
            )
            db.session.add(reg_user)
            db.session.commit()
            app.logger.info("User %s created.", reg_email)
except Exception as _e:
    app.logger.warning("Setup warning: %s", _e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
