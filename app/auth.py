import streamlit as st
import os
import json
from datetime import datetime, timedelta
import jwt
from passlib.hash import pbkdf2_sha256

# In a production app, use a proper database
USERS_FILE = "users.json"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def init_users_file():
    """Initialize the users file if it doesn't exist"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": []}, f)

def get_users():
    """Load users from the JSON file"""
    if not os.path.exists(USERS_FILE):
        return {"users": []}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users_data):
    """Save users to the JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    """Verify password against hashed password"""
    return pbkdf2_sha256.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate password hash"""
    return pbkdf2_sha256.hash(password)

def register_user(username: str, email: str, password: str):
    """Register a new user"""
    users_data = get_users()
    
    # Check if user already exists
    if any(user["username"] == username for user in users_data["users"]):
        return False, "Username already exists"
    if any(user["email"] == email for user in users_data["users"]):
        return False, "Email already registered"
    
    # Create new user
    new_user = {
        "username": username,
        "email": email,
        "hashed_password": get_password_hash(password),
        "full_name": "",
        "disabled": False
    }
    
    users_data["users"].append(new_user)
    save_users(users_data)
    return True, "Registration successful"

def authenticate_user(username: str, password: str):
    """Authenticate user and return token if successful"""
    users_data = get_users()
    user = next((user for user in users_data["users"] if user["username"] == username), None)
    
    if not user or not verify_password(password, user["hashed_password"]):
        return None, "Invalid username or password"
    
    if user.get("disabled"):
        return None, "Account is disabled"
    
    access_token = create_access_token({"sub": user["username"]})
    return access_token, "Login successful"

def get_current_user():
    """Get current user from session state"""
    return st.session_state.get("user")

def is_authenticated():
    """Check if user is authenticated"""
    return "user" in st.session_state and st.session_state.user is not None

def show_login_form():
    """Display login form"""
    with st.form("login_form"):
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            token, message = authenticate_user(username, password)
            if token:
                st.session_state["user"] = username
                st.session_state["token"] = token
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("Don't have an account? **Sign up** below!")

    with st.expander("Create New Account"):
        with st.form("register_form"):
            st.subheader("Create New Account")
            new_username = st.text_input("Choose a username")
            new_email = st.text_input("Email address")
            new_password = st.text_input("Create password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            
            if st.form_submit_button("Sign Up"):
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    success, message = register_user(new_username, new_email, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

def logout():
    """Log out the current user"""
    if "user" in st.session_state:
        del st.session_state["user"]
    if "token" in st.session_state:
        del st.session_state["token"]
    st.rerun()

# Initialize users file when this module is imported
init_users_file()
