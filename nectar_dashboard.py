import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
users_df = pd.read_csv("users.csv")
payments_df = pd.read_csv("payments.csv")
messages_df = pd.read_csv("messages.csv")
conversations_df = pd.read_csv("conversations.csv")

# Ensure datetime columns are properly converted
users_df['created_at'] = pd.to_datetime(users_df['created_at'], errors='coerce')
users_df['last_active'] = pd.to_datetime(users_df['last_active'], errors='coerce')

payments_df['payment_date'] = pd.to_datetime(payments_df['payment_date'], errors='coerce')

messages_df['sent_at'] = pd.to_datetime(messages_df['sent_at'], errors='coerce')

conversations_df['started_at'] = pd.to_datetime(conversations_df['started_at'], errors='coerce')

# Preprocess data
# Calculate metrics
latest_created_at = users_df['created_at'].max()
last_30_days = latest_created_at - pd.Timedelta(days=30)

# Filter users signed up in the last 30 days
recent_users = users_df[users_df['created_at'] >= last_30_days]

# Calculate total revenue for recent users
recent_revenue = payments_df[payments_df['user_id'].isin(recent_users['id'])]['amount'].sum()

# Calculate 30-day conversion rate
converted_users = payments_df[payments_df['user_id'].isin(recent_users['id'])]['user_id'].nunique()
conversion_rate = (converted_users / recent_users.shape[0]) * 100 if recent_users.shape[0] > 0 else 0

# Calculate 30-day retention rate
retained_users = recent_users[recent_users['last_active'] >= last_30_days].shape[0]
retention_rate = (retained_users / recent_users.shape[0]) * 100 if recent_users.shape[0] > 0 else 0

# Active users who sent messages in the last 30 days
active_users = messages_df[messages_df['sent_at'] >= last_30_days]['conversation_id'].nunique()

# Streamlit App
st.title("Customer Retentions and Conversions Rate Report")
st.sidebar.header("Filters")

# Date Range Filter
start_date = st.sidebar.date_input("Start Date", value=last_30_days.date())
end_date = st.sidebar.date_input("End Date", value=latest_created_at.date())

if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
else:
    # Filter data based on date range
    filtered_users = users_df[(users_df['created_at'] >= pd.to_datetime(start_date)) & (users_df['created_at'] <= pd.to_datetime(end_date))]
    filtered_payments = payments_df[payments_df['user_id'].isin(filtered_users['id'])]
    filtered_messages = messages_df[messages_df['sent_at'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

    # Calculate metrics for the filtered data
    filtered_revenue = filtered_payments['amount'].sum()
    filtered_conversion_rate = round((filtered_payments['user_id'].nunique() / filtered_users.shape[0]) * 100, 2) if filtered_users.shape[0] > 0 else 0
    filtered_retention_rate = round((filtered_users[filtered_users['last_active'] >= pd.to_datetime(end_date)].shape[0] / filtered_users.shape[0]) * 100, 2) if filtered_users.shape[0] > 0 else 0

    # Creative Metrics Section
    st.header("Key Metrics")
    st.markdown("""
    <div style="display: flex; justify-content: space-around;">
        <div style="text-align: center;">
            <h3>Total Signups</h3>
            <p style="font-size: 24px; font-weight: bold;">{}</p>
        </div>
        <div style="text-align: center;">
            <h3>Total Revenue</h3>
            <p style="font-size: 24px; font-weight: bold;">${:,.2f}</p>
        </div>
        <div style="text-align: center;">
            <h3>Conversion Rate</h3>
            <p style="font-size: 24px; font-weight: bold;">{:.2f}%</p>
        </div>
        <div style="text-align: center;">
            <h3>Retention Rate</h3>
            <p style="font-size: 24px; font-weight: bold;">{:.2f}%</p>
        </div>
    </div>
    """.format(len(filtered_users), filtered_revenue, filtered_conversion_rate, filtered_retention_rate), unsafe_allow_html=True)

    # Interactive Metric Comparison
    st.header("Interactive Metric Comparison")
    metric_choice = st.selectbox("Select Metric to View:", ["Revenue", "Message Activity", "Retention Funnel"])

    if metric_choice == "Revenue":
        st.subheader("Revenue Trends")
        revenue_trends = filtered_payments.merge(filtered_users[['id', 'created_at']], left_on='user_id', right_on='id')
        revenue_by_date = revenue_trends.groupby(revenue_trends['created_at'].dt.date)['amount'].sum().reset_index()
        fig_revenue = px.bar(revenue_by_date, x='created_at', y='amount', title='Revenue by Date', labels={'created_at': 'Date', 'amount': 'Revenue'})
        st.plotly_chart(fig_revenue)

    elif metric_choice == "Message Activity":
        st.subheader("Message Activity Trends")
        messages_by_date = filtered_messages.groupby(filtered_messages['sent_at'].dt.date).size().reset_index(name='count')
        fig_messages = px.line(messages_by_date, x='sent_at', y='count', title='Messages Sent Over Time', labels={'sent_at': 'Date', 'count': 'Messages Sent'})
        st.plotly_chart(fig_messages)

    elif metric_choice == "Retention Funnel":
        st.subheader("Retention Funnel")
        funnel_data = pd.DataFrame({
            "Stage": ["Signups", "Retained"],
            "Users": [len(filtered_users), filtered_users[filtered_users['last_active'] >= pd.to_datetime(end_date)].shape[0]]
        })
        fig_funnel = px.funnel(funnel_data, x='Users', y='Stage', title='Retention Funnel')
        st.plotly_chart(fig_funnel)

    # Conversion and Retention Rates
    st.header("Conversion and Retention Rates")
    rate_data = pd.DataFrame({
        "Metric": ["Conversion Rate", "Retention Rate"],
        "Value": [round(filtered_conversion_rate,2), round(filtered_retention_rate,2)]
    })
    fig_rates = px.bar(rate_data, x='Metric', y='Value', title='Rates Comparison', labels={'Value': 'Percentage'}, text='Value')
    st.plotly_chart(fig_rates)
