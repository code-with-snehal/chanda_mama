import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import hashlib

st.set_page_config(page_title="Chanda Mama Ultimate", page_icon="🌙", layout="wide")

USERS_FILE = "users.json"
DATA_FILE = "chanda_mama_data.json"

def load_json(file, default={}):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_json(USERS_FILE, {})
app_data = load_json(DATA_FILE, {
    "app_mode": "",
    "master_password": "",
    "groups": {},
    "expenses": []
})

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.mode = app_data.get("app_mode", "")

if not app_data["app_mode"]:
    st.title("🌙 Chanda Mama Ultimate Setup")
    st.info("App ko kaise use karna hai? Mode chuno")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Family Mode")
        st.write("Ek master password. Sab dost same password se login karenge.")
        if st.button("Family Mode Chuno", use_container_width=True):
            app_data["app_mode"] = "family"
            save_json(DATA_FILE, app_data)
            st.rerun()
    with col2:
        st.subheader("2. Private Mode") 
        st.write("Har dost ka alag account. Sign Up/Login.")
        if st.button("Private Mode Chuno", use_container_width=True):
            app_data["app_mode"] = "private"
            save_json(DATA_FILE, app_data)
            st.rerun()
    st.stop()

if app_data["app_mode"] == "family":
    if not app_data["master_password"]:
        st.title("🌙 Family Mode Setup")
        master_pass = st.text_input("Master Password Banao", type="password")
        if st.button("Password Set Karo"):
            if master_pass:
                app_data["master_password"] = hash_password(master_pass)
                save_json(DATA_FILE, app_data)
                st.success("Master Password set! Ab login karo")
                st.rerun()
            else:
                st.error("Password khali nahi ho sakta")
        st.stop()

    if not st.session_state.logged_in:
        st.title("🌙 Chanda Mama - Family Mode")
        password = st.text_input("Master Password Daalo", type="password")
        if st.button("Login"):
            if hash_password(password) == app_data["master_password"]:
                st.session_state.logged_in = True
                st.session_state.username = "FamilyUser"
                st.session_state.mode = "family"
                st.rerun()
            else:
                st.error("Galat Password")
        st.stop()

elif app_data["app_mode"] == "private":
    if not st.session_state.logged_in:
        st.title("🌙 Chanda Mama - Private Mode")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            user = st.text_input("Username", key="login_u")
            pw = st.text_input("Password", type="password", key="login_p")
            if st.button("Login"):
                if user in users and users[user] == hash_password(pw):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.mode = "private"
                    st.rerun()
                else:
                    st.error("Galat Username ya Password")
        with tab2:
            new_user = st.text_input("Naya Username", key="signup_u")
            new_pw = st.text_input("Naya Password", type="password", key="signup_p")
            if st.button("Sign Up"):
                if new_user in users:
                    st.error("Username already exists")
                elif len(new_user) < 3:
                    st.error("Username kam se kam 3 letters ka")
                elif len(new_pw) < 4:
                    st.error("Password kam se kam 4 letters ka")
                else:
                    users[new_user] = hash_password(new_pw)
                    save_json(USERS_FILE, users)
                    st.success("Account ban gaya! Ab Login karo")
        st.stop()

st.sidebar.title(f"🌙 Chanda Mama")
st.sidebar.success(f"Mode: {st.session_state.mode.title()}")
if st.session_state.mode == "private":
    st.sidebar.info(f"User: {st.session_state.username}")

menu = st.sidebar.radio("Menu", ["Dashboard", "Groups", "Kharcha Add", "Hisab-UPI", "Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

if st.session_state.mode == "family":
    my_groups = app_data["groups"]
    my_expenses = app_data["expenses"]
else:
    my_groups = {k:v for k,v in app_data["groups"].items() if st.session_state.username in v["members"]}
    my_expenses = [e for e in app_data["expenses"] if e["group"] in my_groups.keys()]

if menu == "Dashboard":
    st.title("Dashboard - Tera Hisab")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Groups", len(my_groups))
    col2.metric("Total Kharcha", f"₹{sum([e['amount'] for e in my_expenses])}")
    col3.metric("Total Entries", len(my_expenses))

elif menu == "Groups":
    st.title("Groups Manage Karo")
    with st.expander("➕ Naya Group Banao"):
        g_name = st.text_input("Group ka Naam")
        if st.session_state.mode == "private":
            default_members = st.session_state.username
        else:
            default_members = ""
        g_members = st.text_input("Members - comma se alag karo", value=default_members)
        if st.button("Group Banao"):
            if g_name and g_members:
                members_list = [m.strip() for m in g_members.split(",") if m.strip()]
                if st.session_state.mode == "private" and st.session_state.username not in members_list:
                    members_list.append(st.session_state.username)
                if g_name in app_data["groups"]:
                    st.error("Is naam ka group already hai")
                else:
                    app_data["groups"][g_name] = {
                        "members": members_list,
                        "created_by": st.session_state.username,
                        "created_date": str(datetime.now().date())
                    }
                    save_json(DATA_FILE, app_data)
                    st.success(f"Group '{g_name}' ban gaya!")
                    st.rerun()
            else:
                st.error("Naam aur members dono daalo")
    st.subheader("Sabhi Groups")
    if my_groups:
        for g_name, g_data in my_groups.items():
            st.write(f"**{g_name}** - Members: {', '.join(g_data['members'])}")
            st.divider()
    else:
        st.info("Abhi koi group nahi hai")

elif menu == "Kharcha Add":
    st.title("Kharcha Add Karo")
    if not my_groups:
        st.warning("Pehle ek group banao")
    else:
        group = st.selectbox("Group Chuno", list(my_groups.keys()))
        members = my_groups[group]["members"]
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.mode == "private":
                default_idx = members.index(st.session_state.username) if st.session_state.username in members else 0
            else:
                default_idx = 0
            paid_by = st.selectbox("Kisne Diya?", members, index=default_idx)
            amount = st.number_input("Kitna Diya? ₹", min_value=1, step=10)
        with col2:
            desc = st.text_input("Kiska Kharcha?", placeholder="Chai, Petrol")
            date = st.date_input("Date", value=datetime.now())
        if st.button("Kharcha Save Karo", type="primary"):
            expense = {
                "id": len(app_data["expenses"]) + 1,
                "group": group, "paid_by": paid_by, "amount": float(amount),
                "desc": desc, "date": str(date), "added_by": st.session_state.username
            }
            app_data["expenses"].append(expense)
            save_json(DATA_FILE, app_data)
            st.success(f"₹{amount} ka kharcha add ho gaya!")
            st.balloons()

elif menu == "Hisab-UPI":
    st.title("Hisab-UPI - Settle Karo")
    if not my_expenses:
        st.info("Abhi tak koi kharcha nahi hua")
    else:
        group = st.selectbox("Group ka Hisab Dekho", list(my_groups.keys()))
        group_expenses = [e for e in my_expenses if e["group"] == group]
        if group_expenses:
            df = pd.DataFrame(group_expenses)
            total = df["amount"].sum()
            members = my_groups[group]["members"]
            per_person = total / len(members)
            col1, col2 = st.columns(2)
            col1.metric("Total Kharcha", f"₹{total:.2f}")
            col2.metric("Per Person Share", f"₹{per_person:.2f}")
            paid = df.groupby("paid_by")["amount"].sum().to_dict()
            balance = {m: round(paid.get(m, 0) - per_person, 2) for m in members}
            st.subheader("Balance Sheet")
            bal_df = pd.DataFrame(balance.items(), columns=["Member", "Balance"])
            st.dataframe(bal_df, use_container_width=True)
            st.subheader("Kaun Kisko Dega? 💸")
            debtors = sorted([(k, v) for k, v in balance.items() if v < -0.01], key=lambda x: x[1])
            creditors = sorted([(k, v) for k, v in balance.items() if v > 0.01], key=lambda x: x[1], reverse=True)
            if not debtors or not creditors:
                st.success("Sab settled hai! 🎉")
            else:
                i, j = 0, 0
                while i < len(debtors) and j < len(creditors):
                    debtor, d_amt = debtors[i]
                    creditor, c_amt = creditors[j]
                    pay_amt = round(min(abs(d_amt), c_amt), 2)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{debtor}** → **{creditor}**: ₹{pay_amt}")
                    with col2:
                        upi_link = f"upi://pay?pa=snehal@upi&pn={creditor}&am={pay_amt}&cu=INR&tn=ChandaMama-{group}"
                        st.link_button("UPI Pay", upi_link)
                    debtors[i] = (debtor, round(d_amt + pay_amt, 2))
                    creditors[j] = (creditor, round(c_amt - pay_amt, 2))
                    if abs(debtors[i][1]) < 0.01: i += 1
                    if abs(creditors[j][1]) < 0.01: j += 1

elif menu == "Settings":
    st.title("Settings")
    st.warning("⚠️ Danger Zone")
    if st.session_state.mode == "family":
        if st.button("Private Mode pe Switch Karo"):
            app_data["app_mode"] = "private"
            save_json(DATA_FILE, app_data)
            st.session_state.logged_in = False
            st.success("Private Mode activate! Ab Sign Up karo")
            st.rerun()
    else:
        if st.button("Family Mode pe Switch Karo"):
            app_data["app_mode"] = "family"
            app_data["master_password"] = ""
            save_json(DATA_FILE, app_data)
            st.session_state.logged_in = False
            st.success("Family Mode activate! Master password set karo")
            st.rerun()
    st.divider()
    if st.button("🗑️ SARA DATA DELETE KARO", type="secondary"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        if os.path.exists(USERS_FILE): os.remove(USERS_FILE)
        st.success("Sab delete ho gaya! Refresh karo")
        st.rerun()