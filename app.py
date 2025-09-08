import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# تنظیم پایگاه داده
def init_db():
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    # جدول کاربران
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL, -- 'athlete' یا 'coach'
            password TEXT NOT NULL,
            profile_picture TEXT
        )
    ''')
    # اضافه کردن ستون profile_picture اگه وجود نداشته باشه
    try:
        c.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
    except sqlite3.OperationalError:
        pass  # ستون قبلاً وجود داره
    # جدول اتصال ورزشکار به مربی
    c.execute('''
        CREATE TABLE IF NOT EXISTS athlete_coach (
            athlete_id TEXT,
            coach_id TEXT,
            PRIMARY KEY (athlete_id, coach_id),
            FOREIGN KEY (athlete_id) REFERENCES users(user_id),
            FOREIGN KEY (coach_id) REFERENCES users(user_id)
        )
    ''')
    # جدول تمرینات
    c.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete_id TEXT NOT NULL,
            date TEXT NOT NULL,
            goal TEXT,
            muscles TEXT,
            type TEXT,
            duration INTEGER,
            intensity INTEGER,
            recorded_by TEXT,
            FOREIGN KEY (athlete_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

# تابع برای ثبت کاربر جدید
def register_user(user_id, name, role, password, profile_picture):
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (user_id, name, role, password, profile_picture) VALUES (?, ?, ?, ?, ?)", 
                  (user_id, name, role, password, profile_picture))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # user_id تکراریه
    finally:
        conn.close()

# تابع برای ورود کاربر
def login_user(user_id, password):
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    c.execute("SELECT role, name, profile_picture FROM users WHERE user_id = ? AND password = ?", 
              (user_id, password))
    result = c.fetchone()
    conn.close()
    return result if result else None

# تابع برای اتصال ورزشکار به مربی
def link_athlete_to_coach(athlete_id, coach_id):
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO athlete_coach (athlete_id, coach_id) VALUES (?, ?)", 
                  (athlete_id, coach_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # اتصال تکراری یا خطا
    finally:
        conn.close()

# تابع برای چک کردن دسترسی
def has_access(user_id, athlete_id):
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    # اگر کاربر خودش ورزشکاره
    if user_id == athlete_id:
        return True
    # اگر کاربر مربیه
    c.execute("SELECT 1 FROM athlete_coach WHERE athlete_id = ? AND coach_id = ?", 
              (athlete_id, user_id))
    result = c.fetchone()
    conn.close()
    return bool(result)

# تابع برای ثبت تمرین
def save_workout(athlete_id, date, goal, muscles, type, duration, intensity, recorded_by):
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO workouts (athlete_id, date, goal, muscles, type, duration, intensity, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (athlete_id, date, goal, muscles, type, duration, intensity, recorded_by))
    conn.commit()
    conn.close()

# تابع برای گرفتن تاریخچه
def get_workouts(athlete_id):
    conn = sqlite3.connect("workouts.db")
    c = conn.cursor()
    c.execute("SELECT * FROM workouts WHERE athlete_id = ?", (athlete_id,))
    workouts = c.fetchall()
    conn.close()
    return workouts

# رابط کاربری
st.title("اپلیکیشن ثبت تمرین ورزشی")
init_db()

# مدیریت حالت ورود
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.role = None
    st.session_state.name = None
    st.session_state.profile_picture = None

# فرم ورود در نوار کناری
st.sidebar.header("ورود")
user_id = st.sidebar.text_input("شناسه کاربر")
password = st.sidebar.text_input("رمز عبور", type="password")
if st.sidebar.button("ورود"):
    user_info = login_user(user_id, password)
    if user_info:
        st.session_state.user_id = user_id
        st.session_state.role = user_info[0]
        st.session_state.name = user_info[1]
        st.session_state.profile_picture = user_info[2]
        st.sidebar.success(f"خوش آمدید، {st.session_state.name} ({st.session_state.role})")
    else:
        st.sidebar.error("شناسه یا رمز عبور اشتباه است.")

# فرم ثبت‌نام در نوار کناری
st.sidebar.header("ثبت‌نام")
new_user_id = st.sidebar.text_input("شناسه جدید")
new_name = st.sidebar.text_input("نام")
new_role = st.sidebar.selectbox("نقش", ["ورزشکار", "مربی"])
new_password = st.sidebar.text_input("رمز عبور جدید", type="password")
new_profile_picture = st.sidebar.text_input("URL عکس پروفایل (اختیاری)")
if st.sidebar.button("ثبت‌نام"):
    if register_user(new_user_id, new_name, new_role, new_password, new_profile_picture):
        st.sidebar.success("کاربر با موفقیت ثبت شد!")
    else:
        st.sidebar.error("شناسه قبلاً استفاده شده است.")

# نمایش هدر با نام و عکس
if st.session_state.user_id:
    st.markdown(f"""
        <div style='display: flex; align-items: center;'>
            <h2>خوش آمدید، {st.session_state.name}</h2>
        </div>
    """, unsafe_allow_html=True)
    if st.session_state.profile_picture:
        st.image(st.session_state.profile_picture, width=100)

    # فرم اتصال ورزشکار به مربی (فقط برای مربی)
    if st.session_state.role == "مربی":
        st.header("اتصال ورزشکار به مربی")
        athlete_id_to_link = st.text_input("شناسه ورزشکار برای اتصال")
        if st.button("اتصال"):
            if link_athlete_to_coach(athlete_id_to_link, st.session_state.user_id):
                st.success(f"ورزشکار {athlete_id_to_link} به شما متصل شد.")
            else:
                st.error("خطا در اتصال. مطمئن شوید شناسه ورزشکار معتبر است.")

    # فرم ثبت تمرین
    st.header("ثبت تمرین")
    with st.form("workout_form"):
        athlete_id = st.text_input("شناسه ورزشکار (مثل نام یا ID)")
        goal = st.text_input("هدف جلسه (مثل چربی‌سوزی، عضله سازی و ...)")
        muscles = st.text_input("عضلات درگیر (مثل سینه، شانه، فول بادی و ...)")
        type = st.text_input("نوع تمرین (مثل دایره ای، سوپر ست، تریپل و ...)")  # تغییر به text_input
        duration = st.number_input("مدت زمان (دقیقه)", min_value=0, step=1)
        intensity = st.slider("شدت تمرین (1 تا 10)", 1, 10, 5)
        recorded_by = st.selectbox("ثبت‌کننده", ["ورزشکار", "مربی"])
        submit = st.form_submit_button("ثبت تمرین")

        if submit:
            if athlete_id and type and has_access(st.session_state.user_id, athlete_id):
                date = datetime.now().strftime("%Y-%m-%d")
                save_workout(athlete_id, date, goal, muscles, type, duration, intensity, recorded_by)
                st.success("تمرین با موفقیت ثبت شد!")
            else:
                st.error("شناسه ورزشکار یا نوع تمرین نامعتبر است یا دسترسی ندارید.")

    # نمایش تاریخچه
    st.header("تاریخچه تمرینات")
    athlete_id_history = st.text_input("شناسه ورزشکار برای مشاهده تاریخچه")
    if athlete_id_history and has_access(st.session_state.user_id, athlete_id_history):
        workouts = get_workouts(athlete_id_history)
        if workouts:
            df = pd.DataFrame(workouts, columns=["ID", "Athlete ID", "Date", "Goal", "Muscles", "Type", "Duration", "Intensity", "Recorded By"])
            st.table(df)
        else:
            st.write("هیچ تمرینی برای این ورزشکار ثبت نشده.")
    elif athlete_id_history:
        st.error("شما به تمرینات این ورزشکار دسترسی ندارید.")
else:
    st.warning("لطفاً ابتدا وارد شوید.")