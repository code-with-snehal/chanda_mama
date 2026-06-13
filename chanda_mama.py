import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import hashlib
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Chanda Mama Ultimate Pro", page_icon="🌙", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# ========== HELPER FUNCTIONS ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_sheet(sheet_name, columns):
    try:
        data = conn.read(worksheet=sheet_name, ttl=5)
        data = data.dropna(how="all")
        if data.empty:
            return pd.DataFrame(columns=columns)
        return data
    except:
        return pd.DataFrame(columns=columns)

def save_sheet(sheet_name, df):
    conn.update(worksheet=sheet_name, data=df)

def rerun():
    st.rerun()

# ========== LOAD ALL DATA ==========
config_df = load_sheet("Config", ['app_mode', 'master_password'])
users_df = load_sheet("Users", ['username', 'password'])
expenses_df = load_sheet("Expenses", ['id', 'Date', 'Category', 'Amount', 'Note', 'Username', 'Group'])
groups_df = load_sheet("Groups", ['GroupName', 'Members'])

config = config_df.iloc[0].to_dict() if not config_df.empty else {"app_mode": "", "master_password": ""}

# ========== SESSION STATE ==========
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.mode = config.get("app_mode", "")
    st.session_state.edit_id = None

# ========== SETUP SCREEN ==========
if not config["app_mode"]:
    st.title("🌙 Chanda Mama Ultimate Pro Setup")
    st.info("App ko kaise use karna hai? Mode chuno")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Family Mode")
        st.write("Ek master password. Sab dost same password se login karenge. Hisaab common.")
        if st.button("Family Mode Chuno", use_container_width=True, type="primary"):
            config_df = pd.DataFrame([{"app_mode": "family", "master_password": ""}])
            save_sheet("Config", config_df)
            rerun()
    with col2:
        st.subheader("2. Private Mode")
        st.write("Har dost ka alag account. Sign Up/Login. Personal + Group hisaab.")
        if st.button("Private Mode Chuno", use_container_width=True, type="primary"):
            config_df = pd.DataFrame([{"app_mode": "private", "master_password": ""}])
            save_sheet("Config", config_df)
            rerun()
    st.stop()

# ========== FAMILY MODE LOGIN ==========
if config["app_mode"] == "family":
    if not config["master_password"]:
        st.title("🌙 Family Mode - Master Password Setup")
        master_pass = st.text_input("Master Password Banao", type="password")
        if st.button("Password Set Karo", type="primary"):
            if master_pass and len(master_pass) >= 4:
                config["master_password"] = hash_password(master_pass)
                save_sheet("Config", pd.DataFrame([config]))
                st.success("Master Password set! Ab login karo")
                rerun()
            else:
                st.error("Password kam se kam 4 letters ka daalo")
        st.stop()

    if not st.session_state.logged_in:
        st.title("🌙 Chanda Mama - Family Mode")
        password = st.text_input("Master Password Daalo", type="password")
        if st.button("Login", type="primary"):
            if hash_password(password) == config["master_password"]:
                st.session_state.logged_in = True
                st.session_state.username = "FamilyUser"
                st.session_state.mode = "family"
                rerun()
            else:
                st.error("Galat Password")
        st.stop()

# ========== PRIVATE MODE LOGIN ==========
elif config["app_mode"] == "private":
    if not st.session_state.logged_in:
        st.title("🌙 Chanda Mama - Private Mode")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            user = st.text_input("Username", key="login_u")
            pw = st.text_input("Password", type="password", key="login_p")
            if st.button("Login", type="primary"):
                hashed = hash_password(pw)
                user_match = users_df[(users_df['username'] == user) & (users_df['password'] == hashed)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.mode = "private"
                    rerun()
                else:
                    st.error("Galat Username ya Password")
        with tab2:
            new_user = st.text_input("Naya Username", key="signup_u")
            new_pw = st.text_input("Naya Password", type="password", key="signup_p")
            if st.button("Sign Up", type="primary"):
                if new_user in users_df['username'].values:
                    st.error("Username already exists")
                elif len(new_user) < 3:
                    st.error("Username kam se kam 3 letters ka")
                elif len(new_pw) < 4:
                    st.error("Password kam se kam 4 letters ka")
                else:
                    new_data = pd.DataFrame([{'username': new_user, 'password': hash_password(new_pw)}])
                    users_df = pd.concat([users_df, new_data], ignore_index=True)
                    save_users(users_df)
                    st.success("Account ban gaya! Login karo")
        st.stop()

# ========== MAIN APP ==========
st.sidebar.title(f"Hi, {st.session_state.username} 🌙")
st.sidebar.caption(f"Mode: {st.session_state.mode.title()}")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.edit_id = None
    rerun()

menu = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Add Expense", "👥 Groups", "📈 Group Hisaab"])

# Filter data based on mode
if st.session_state.mode == "private":
    user_expenses = expenses_df[expenses_df['Username'] == st.session_state.username].copy()
else:
    user_expenses = expenses_df.copy()

user_expenses['Amount'] = pd.to_numeric(user_expenses['Amount'], errors='coerce').fillna(0)
user_expenses['Date'] = pd.to_datetime(user_expenses['Date'], errors='coerce')

# ========== DASHBOARD ==========
if menu == "📊 Dashboard":
    st.title("📊 Dashboard - Tera Hisab Kitab")

    if user_expenses.empty:
        st.info("Abhi tak koi expense nahi. 'Add Expense' se shuru kar!")
    else:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Start Date", user_expenses['Date'].min().date())
        with col2:
            end_date = st.date_input("End Date", user_expenses['Date'].max().date())
        with col3:
            cat_filter = st.multiselect("Category", user_expenses['Category'].unique(), default=user_expenses['Category'].unique())

        mask = (user_expenses['Date'].dt.date >= start_date) & (user_expenses['Date'].dt.date <= end_date) & (user_expenses['Category'].isin(cat_filter))
        filtered_df = user_expenses[mask]

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Kharcha", f"₹{filtered_df['Amount'].sum():,.2f}")
        col2.metric("Total Entries", len(filtered_df))
        col3.metric("Avg per Day", f"₹{filtered_df['Amount'].sum()/max(len(filtered_df['Date'].dt.date.unique()),1):,.2f}")
        col4.metric("Top Category", filtered_df.groupby('Category')['Amount'].sum().idxmax() if not filtered_df.empty else "N/A")

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            cat_data = filtered_df.groupby('Category')['Amount'].sum().reset_index()
            fig = px.pie(cat_data, values='Amount', names='Category', title='Category Wise Kharcha')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            daily_data = filtered_df.groupby(filtered_df['Date'].dt.date)['Amount'].sum().reset_index()
            fig = px.bar(daily_data, x='Date', y='Amount', title='Daily Kharcha')
            st.plotly_chart(fig, use_container_width=True)

        # Table with Delete/Edit
        st.subheader("Sabhi Expenses")
        for idx, row in filtered_df.sort_values('Date', ascending=False).iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2,2,2,2,2,1,1])
            col1.write(row['Date'].strftime("%d-%b-%Y"))
            col2.write(row['Category'])
            col3.write(f"₹{row['Amount']:.2f}")
            col4.write(row['Note'])
            col5.write(row['Group'])
            if col6.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_id = row['id']
                rerun()
            if col7.button("🗑️", key=f"del_{row['id']}"):
                expenses_df = expenses_df[expenses_df['id']!= row['id']]
                save_sheet("Expenses", expenses_df)
                st.success("Deleted!")
                rerun()

        # Export
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, f"expenses_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# ========== ADD/EDIT EXPENSE ==========
elif menu == "➕ Add Expense":
    if st.session_state.edit_id:
        st.title("✏️ Edit Expense")
        edit_row = expenses_df[expenses_df['id'] == st.session_state.edit_id].iloc[0]
    else:
        st.title("➕ Add Expense")
        edit_row = None

    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.date_input("Date", value=pd.to_datetime(edit_row['Date']).date() if edit_row is not None else date.today())
            category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Rent", "Health", "Entertainment", "Other"],
                                   index=["Food", "Travel", "Shopping", "Bills", "Rent", "Health", "Entertainment", "Other"].index(edit_row['Category']) if edit_row is not None else 0)
        with col2:
            amount = st.number_input("Amount ₹", min_value=0.0, format="%.2f", value=float(edit_row['Amount']) if edit_row is not None else 0.0)
            note = st.text_input("Note", value=edit_row['Note'] if edit_row is not None else "")

        if st.session_state.mode == "private":
            user_groups = groups_df[groups_df['Members'].str.contains(st.session_state.username, na=False)]['GroupName'].tolist()
            group_options = ["Personal"] + user_groups
            group = st.selectbox("Group", group_options, index=group_options.index(edit_row['Group']) if edit_row is not None and edit_row['Group'] in group_options else 0)
        else:
            group = "Family"

        if st.form_submit_button("💾 Save", type="primary"):
            if amount <= 0:
                st.error("Amount 0 se zyada hona chahiye")
            else:
                if st.session_state.edit_id: # Update
                    expenses_df.loc[expenses_df['id'] == st.session_state.edit_id, ['Date', 'Category', 'Amount', 'Note', 'Group']] = [
                        exp_date.strftime("%Y-%m-%d"), category, amount, note, group
                    ]
                    st.session_state.edit_id = None
                    msg = "Expense Updated!"
                else: # Add new
                    new_id = int(expenses_df['id'].max()) + 1 if not expenses_df.empty else 1
                    new_data = pd.DataFrame([{
                        'id': new_id,
                        'Date': exp_date.strftime("%Y-%m-%d"),
                        'Category': category,
                        'Amount': amount,
                        'Note': note,
                        'Username': st.session_state.username,
                        'Group': group
                    }])
                    expenses_df = pd.concat([expenses_df, new_data], ignore_index=True)
                    msg = "Expense Added!"

                save_sheet("Expenses", expenses_df)
                st.success(msg)
                rerun()

    if st.session_state.edit_id:
        if st.button("Cancel Edit"):
            st.session_state.edit_id = None
            rerun()

# ========== GROUPS ==========
elif menu == "👥 Groups":
    st.title("👥 Manage Groups")
    if st.session_state.mode == "private":
        with st.expander("➕ Naya Group Banao", expanded=False):
            g_name = st.text_input("Group ka Naam")
            all_users = users_df['username'].tolist()
            g_members = st.multiselect("Members Select Karo", all_users, default=[st.session_state.username])
            if st.button("Group Banao", type="primary"):
                if not g_name:
                    st.error("Group ka naam daalo")
                elif g_name in groups_df['GroupName'].values:
                    st.error("Is naam ka group already hai")
                elif not g_members:
                    st.error("Kam se kam 1 member chahiye")
                else:
                    if st.session_state.username not in g_members:
                        g_members.append(st.session_state.username)
                    new_group = pd.DataFrame([{'GroupName': g_name, 'Members': ",".join(g_members)}])
                    groups_df = pd.concat([groups_df, new_group], ignore_index=True)
                    save_sheet("Groups", groups_df)
                    st.success(f"Group '{g_name}' ban gaya!")
                    rerun()

        st.subheader("Tere Groups")
        my_groups = groups_df[groups_df['Members'].str.contains(st.session_state.username, na=False)]
        if my_groups.empty:
            st.info("Tu kisi group mein nahi hai")
        else:
            for idx, row in my_groups.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3,3,1])
                    col1.write(f"**{row['GroupName']}**")
                    col2.write(f"Members: {row['Members']}")
                    if col3.button("🗑️", key=f"delgrp_{row['GroupName']}"):
                        groups_df = groups_df[groups_df['GroupName']!= row['GroupName']]
                        save_sheet("Groups", groups_df)
                        st.success("Group deleted!")
                        rerun()
    else:
        st.info("Family Mode mein Groups nahi hote. Sabka hisaab ek saath.")

# ========== GROUP HISAAB ==========
elif menu == "📈 Group Hisaab":
    st.title("📈 Group Hisaab-Kitab")
    if st.session_state.mode == "private":
        my_groups = groups_df[groups_df['Members'].str.contains(st.session_state.username, na=False)]['GroupName'].tolist()
        if not my_groups:
            st.info("Tu kisi group mein nahi hai")
        else:
            selected_group = st.selectbox("Group Chuno", my_groups)
            group_expenses = expenses_df[expenses_df['Group'] == selected_group].copy()
            group_expenses['Amount'] = pd.to_numeric(group_expenses['Amount'], errors='coerce')

            if group_expenses.empty:
                st.info(f"'{selected_group}' mein abhi tak koi expense nahi")
            else:
                total = group_expenses['Amount'].sum()
                members = groups_df[groups_df['GroupName'] == selected_group]['Members'].iloc[0].split(",")
                per_person = total / len(members)

                st.metric(f"Total Group Kharcha", f"₹{total:,.2f}")
                st.metric(f"Per Person Hissa", f"₹{per_person:,.2f}")

                # Kisne kitna diya
                paid_data = group_expenses.groupby('Username')['Amount'].sum().reset_index()
                st.subheader("Kisne Kitna Pay Kiya")

                result_data = []
                for member in members:
                    paid = paid_data[paid_data['Username'] == member]['Amount'].sum()
                    balance = paid - per_person
                    result_data.append({
                        'Member': member,
                        'Paid': f"₹{paid:,.2f}",
                        'Hissa': f"₹{per_person:,.2f}",
                        'Balance': f"₹{balance:,.2f}",
                        'Status': "Lena Hai" if balance < 0 else "Dena Hai" if balance > 0 else "Settled"
                    })

                st.dataframe(pd.DataFrame(result_data), use_container_width=True)

                # Chart
                fig = px.bar(paid_data, x='Username', y='Amount', title=f'{selected_group} - Kisne Kitna Diya')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Family Mode mein ye feature nahi hai. Sabka hisaab common hai.")
