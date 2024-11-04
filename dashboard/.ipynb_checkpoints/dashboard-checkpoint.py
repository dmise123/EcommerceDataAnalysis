import pandas as pd
import streamlit as st
import altair as alt
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns  
import matplotlib.ticker as ticker


# Fungsi untuk memformat ID pelanggan
def format_customer_id(customer_id):
    return customer_id[:3] + '...' if len(customer_id) > 3 else customer_id

# Fungsi untuk analisis penjualan bulanan
def monthly_sales_analysis(df):
    monthly_sales = df.groupby(df['order_purchase_timestamp'].dt.to_period('M')).agg({'payment_value': 'sum'}).reset_index()
    return monthly_sales

# Fungsi untuk analisis penjualan harian
def daily_sales_analysis(df):
    daily_sales = df.groupby(df['order_purchase_timestamp'].dt.date).agg({'payment_value': 'sum', 'order_id': 'count'}).reset_index()
    daily_sales.rename(columns={'order_id': 'order_count', 'payment_value': 'revenue', 'order_purchase_timestamp': 'order_date'}, inplace=True)
    return daily_sales

# Fungsi untuk analisis metode pembayaran
def payment_type_analysis(df):
    sales_by_payment = df.groupby('payment_type')['payment_value'].sum().sort_values(ascending=False).reset_index()
    return sales_by_payment

# Fungsi untuk membuat DataFrame RFM
def create_rfm_df(df, reference_date, months_back):
    df.loc[:, 'order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    period_start = reference_date - pd.DateOffset(months=months_back)
    df_recent = df[df['order_purchase_timestamp'] >= period_start]

    rfm_df = df_recent.groupby("customer_id", as_index=False).agg({
        "payment_value": "sum",
        "order_purchase_timestamp": "count",
        "month_last_purchase": "max"
    })
    
    rfm_df.rename(columns={
        "payment_value": "monetary",
        "order_purchase_timestamp": "frequency",
        "month_last_purchase": "recency"
    }, inplace=True)

    top_10_customers = rfm_df.nlargest(10, 'monetary')
    return rfm_df, top_10_customers

# Fungsi untuk mengkategorikan pelanggan
def categorize_customers(df):
    categorize_customer_count = df.groupby('category')['customer_id'].nunique().reset_index(name='customer_count')
    return categorize_customer_count
    
# Fungsi untuk analisis lokasi penjual
def location_analysis(df):
    city_seller_counts = df.groupby('seller_city').customer_id.nunique().sort_values(ascending=False).reset_index()
    state_seller_counts = df.groupby('seller_state').customer_id.nunique().sort_values(ascending=False).reset_index()
    return city_seller_counts, state_seller_counts

# Fungsi untuk analisis kategori produk dengan penjualan tertinggi di setiap negara bagian
def top_product_category_by_state(df):
    category_state_sales = df.groupby(['seller_state', 'product_category_name']).agg({
        "payment_value": "sum"
    }).reset_index()
    top_category_by_state = category_state_sales.loc[category_state_sales.groupby('seller_state')['payment_value'].idxmax()]
    return top_category_by_state

# Fungsi untuk memformat angka sebagai mata uang
def format_currency(amount):
    """Format angka sebagai mata uang USD."""
    # Menggunakan format string untuk menambahkan koma sebagai pemisah ribuan
    return f"${amount:,.2f}"  # Menampilkan dua desimal untuk Dolar


# Main program
df_all = pd.read_csv("dashboard/all_data.csv")
df_all['order_purchase_timestamp'] = pd.to_datetime(df_all['order_purchase_timestamp'])

# Sidebar untuk input tanggal
st.sidebar.header("Filter Data berdasarkan Tanggal")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime('2018-01-01'))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime('2018-10-31'))

# Filter data di range tanggal yang dipilih
df_filtered = df_all[(df_all['order_purchase_timestamp'] >= pd.to_datetime(start_date)) & 
                     (df_all['order_purchase_timestamp'] <= pd.to_datetime(end_date))]

months_back = 5
reference_date = pd.to_datetime('2018-10-31')

# RFM Analysis
rfm_df, top_10_customers = create_rfm_df(df_filtered, reference_date, months_back)

# Analisis Kategori Produk berdasarkan Negara Bagian
top_category_by_state = top_product_category_by_state(df_filtered)
daily_orders_df = daily_sales_analysis(df_filtered)

# Mendapatkan jumlah pelanggan berdasarkan kategori
customer_category_counts = categorize_customers(df_filtered)

# Tampilan Aplikasi Streamlit
st.title("Dashboard Analisis Data E-commerce")
# Metrik Pesanan Harian
st.subheader("Analisis Penjualan Harian")
col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total Pesanan", value=total_orders)

with col2:
    total_revenue = daily_orders_df.revenue.sum()
    formatted_revenue = format_currency(total_revenue)  # Dengan ini
    st.metric("Total Pendapatan", value=formatted_revenue)


# Plotting pendapatan pesanan harian
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_date"],
    daily_orders_df["revenue"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)


# Analisis Penjualan Bulanan
st.subheader("Analisis Penjualan Bulanan")
monthly_sales = monthly_sales_analysis(df_filtered)
st.line_chart(monthly_sales.set_index('order_purchase_timestamp')['payment_value'])


# Tampilan RFM
st.subheader("Pelanggan Terbaik Berdasarkan Parameter RFM")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(df_filtered['month_last_purchase'].mean(), 2)
    st.metric("Average Recency (month)", value=avg_recency)

with col2:
    
    avg_frequency = round(rfm_df['frequency'].mean(), 2)  
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df['monetary'].mean())  
    st.metric("Average Monetary", value=avg_monetary)

# Menambahkan ID pelanggan yang diformat
rfm_df['formatted_customer_id'] = rfm_df['customer_id'].apply(format_customer_id)

# Plotting metrik RFM
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9"] * 5

# Plotting Recency
sns.barplot(
    y="recency", 
    x="formatted_customer_id",  
    data=rfm_df.sort_values(by="recency", ascending=True).head(5), 
    hue='formatted_customer_id',  # Added hue parameter
    palette=colors, 
    legend=False,  # Disable the legend if it's not needed
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Customer ID", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)


# Plotting Frekuensi
sns.barplot(
    y="frequency", 
    x="formatted_customer_id",  
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5), 
    hue='formatted_customer_id',  
    palette=colors, 
    legend=False,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Customer ID", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)

# Plottinh Monetary
sns.barplot(
    y="monetary", 
    x="formatted_customer_id",  
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5), 
    hue='formatted_customer_id',  
    palette=colors, 
    legend=False,
    ax=ax[2]
)
ax[2].set_ylabel(None)
ax[2].set_xlabel("Customer ID", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)

# Menampilkan plot di Streamlit
st.pyplot(fig)

# Analisis Lokasi Penjual
st.subheader("Analisis Lokasi Penjual")
city_seller_counts, state_seller_counts = location_analysis(df_filtered)

# Analisis pelanggan unik berdasarkan kota
top_cities = city_seller_counts.nlargest(20, 'customer_id')

city_chart = alt.Chart(top_cities).mark_bar().encode(
    x=alt.X('customer_id:Q', title='Jumlah Pelanggan Unik'),
    y=alt.Y('seller_city:N', title='Kota', sort='-x'),
    tooltip=['seller_city', 'customer_id']
).properties(
    title="Top 20 Kota dengan Jumlah Pelanggan Unik",
    width=700,
    height=400
)

st.altair_chart(city_chart, use_container_width=True)

# Analisis pelanggan unik berdasarkan Negara Bagian
state_chart = alt.Chart(state_seller_counts).mark_bar().encode(
    x=alt.X('customer_id:Q', title='Jumlah Pelanggan Unik'),
    y=alt.Y('seller_state:N', title='Negara Bagian', sort='-x'),
    tooltip=['seller_state', 'customer_id']
).properties(
    title="Jumlah Pelanggan Unik Berdasarkan Negara Bagian Penjual",
    width=700,
    height=400
)
st.altair_chart(state_chart, use_container_width=True)

# Analisis Kategori Produk Teratas di Setiap Negara Bagian
st.subheader("Kategori Produk dengan Penjualan Tertinggi di Setiap Negara Bagian")

chart = alt.Chart(top_category_by_state).mark_bar().encode(
    x=alt.X('payment_value:Q', title='Total Penjualan'),
    y=alt.Y('seller_state:N', title='Negara Bagian', sort='-x'),
    color='product_category_name:N',
    tooltip=['seller_state', 'product_category_name', 'payment_value']
).properties(
    width=700,
    height=400,
    title="Kategori Produk Teratas Berdasarkan Penjualan di Setiap Negara Bagian"
)

# Display chart di Streamlit
st.altair_chart(chart, use_container_width=True)

st.subheader("Jumlah Pelanggan Berdasarkan Kategori")
st.bar_chart(customer_category_counts.set_index('category')['customer_count'])
