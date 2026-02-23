import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ======================
# PAGE CONFIGURATION
# ======================
st.set_page_config(
    page_title="OEE Production Dashboard",
    page_icon="🏭",
    layout="wide"  # uses full screen width
)

# ======================
# FILE UPLOAD + DATA LOADING
# ======================

def load_default_data():
    try:
        df = pd.read_csv('oee_data.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        st.error("⚠️ Default dataset not found. Please upload your OEE data file using the uploader in the sidebar.")
        st.stop()

def load_uploaded_file(uploaded_file):
    # Detect if CSV or Excel and load accordingly
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(uploaded_file)
    else:
        return None, "❌ Unsupported file type. Please upload CSV or Excel."
    
    # Check required columns exist
    required_columns = [
        'date', 'machine', 'shift',
        'planned_time_min', 'downtime_min', 'run_time_min',
        'availability', 'performance', 'quality',
        'oee', 'total_parts', 'good_parts', 'downtime_reason'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        return None, f"❌ Missing columns: {', '.join(missing)}"
    
    # Fix date column
    df['date'] = pd.to_datetime(df['date'])
    
    return df, "✅ File loaded successfully!"

# --- Upload widget in sidebar ---
uploaded_file = None

st.sidebar.header("📂 Data Source")

UPLOAD_PASSWORD = "oee2024"

uploaded_file = None

with st.sidebar.expander("🔐 Upload Access"):
    entered_password = st.text_input(
        "Enter access code",
        type="password",
        placeholder="••••••••"
    )

    if entered_password == UPLOAD_PASSWORD:
        st.success("✅ Access granted")
        uploaded_file = st.file_uploader(
            "Upload your OEE data (CSV or Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="File must contain the standard OEE columns"
        )
        try:
            template_df = pd.read_csv('oee_data.csv').head(5)
            template_csv = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Template",
                data=template_csv,
                file_name='oee_template.csv',
                mime='text/csv'
            )
        except:
            pass
    elif entered_password != "":
        st.error("❌ Incorrect access code")

if uploaded_file is not None:
    df, message = load_uploaded_file(uploaded_file)
    if df is None:
        st.sidebar.error(message)
        st.stop()  # stop the app if file is invalid
    else:
        st.sidebar.success(message)
        st.sidebar.markdown(f"📊 **{len(df):,} rows loaded**")
        data_source = f"📂 {uploaded_file.name}"
else:
    df = load_default_data()
    data_source = "📂 Default Dataset (oee_data.csv)"

st.sidebar.caption(f"Source: {data_source}")

# --- Template download so clients know the format ---
template_df = pd.read_csv('oee_data.csv').head(5)
template_csv = template_df.to_csv(index=False).encode('utf-8')

st.sidebar.download_button(
    label="⬇️ Download Template",
    data=template_csv,
    file_name='oee_template.csv',
    mime='text/csv',
    help="Download this template, fill with your data, then upload"
)

# ======================
# TITLE
# ======================
st.title("🏭 OEE Production Dashboard")
st.markdown("**Overall Equipment Effectiveness — Manufacturing Performance Tracker**")
st.divider()
# ======================
# SIDEBAR FILTERS
# ======================
st.sidebar.header("🔧 Filters")

# Machine filter
all_machines = df['machine'].unique().tolist()
selected_machines = st.sidebar.multiselect(
    "Select Machines",
    options=all_machines,
    default=all_machines  # all selected by default
)

# Shift filter
all_shifts = df['shift'].unique().tolist()
selected_shifts = st.sidebar.multiselect(
    "Select Shifts",
    options=all_shifts,
    default=all_shifts
)

# Date range filter
min_date = df['date'].min()
max_date = df['date'].max()
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# ======================
# FILTER THE DATAFRAME
# ======================
filtered_df = df[
    (df['machine'].isin(selected_machines)) &
    (df['shift'].isin(selected_shifts)) &
    (df['date'] >= pd.Timestamp(start_date)) &
    (df['date'] <= pd.Timestamp(end_date))
]

# Show how many rows are loaded
st.sidebar.markdown(f"📊 **{len(filtered_df):,} records loaded**")
# ======================
# KPI CALCULATIONS
# ======================
avg_oee = filtered_df['oee'].mean()
avg_availability = filtered_df['availability'].mean()
avg_performance = filtered_df['performance'].mean()
avg_quality = filtered_df['quality'].mean()
total_good_parts = filtered_df['good_parts'].sum()
total_downtime = filtered_df['downtime_min'].sum()

# ======================
# KPI CARDS ROW
# ======================
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        label="🏭 Overall OEE",
        value=f"{avg_oee:.1%}",
        delta=f"{avg_oee - 0.85:.1%} vs World Class"
    )

with col2:
    st.metric(
        label="⏱️ Availability",
        value=f"{avg_availability:.1%}",
    )

with col3:
    st.metric(
        label="⚡ Performance",
        value=f"{avg_performance:.1%}",
    )

with col4:
    st.metric(
        label="✅ Quality",
        value=f"{avg_quality:.1%}",
    )

with col5:
    st.metric(
        label="🔩 Good Parts",
        value=f"{total_good_parts:,}",
    )

with col6:
    st.metric(
        label="🔴 Total Downtime",
        value=f"{total_downtime:,} min",
    )

st.divider()
# ======================
# ROW 1 — OEE TREND + DOWNTIME PARETO
# ======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 OEE Trend Over Time")
    
    # Group by date and calculate daily average OEE
    oee_trend = filtered_df.groupby('date')['oee'].mean().reset_index()
    
    fig_trend = px.line(
        oee_trend,
        x='date',
        y='oee',
        title='Daily Average OEE',
        labels={'oee': 'OEE', 'date': 'Date'},
        color_discrete_sequence=['#00CC96']
    )
    
    # Add world class benchmark line at 85%
    fig_trend.add_hline(
        y=0.85,
        line_dash='dash',
        line_color='red',
        annotation_text='World Class (85%)'
    )
    
    fig_trend.update_layout(yaxis_tickformat='.0%')
    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    st.subheader("📊 Downtime by Reason (Pareto)")
    
    # Sum downtime per reason and sort descending
    pareto = filtered_df.groupby('downtime_reason')['downtime_min'].sum()
    pareto = pareto.sort_values(ascending=False).reset_index()
    
    # Calculate cumulative percentage — this is what makes it a Pareto
    pareto['cumulative_pct'] = pareto['downtime_min'].cumsum() / pareto['downtime_min'].sum() * 100
    
    fig_pareto = go.Figure()
    
    # Bars for downtime minutes
    fig_pareto.add_trace(go.Bar(
        x=pareto['downtime_reason'],
        y=pareto['downtime_min'],
        name='Downtime (min)',
        marker_color='#EF553B'
    ))
    
    # Line for cumulative percentage
    fig_pareto.add_trace(go.Scatter(
        x=pareto['downtime_reason'],
        y=pareto['cumulative_pct'],
        name='Cumulative %',
        yaxis='y2',
        line=dict(color='#FFA15A', width=2),
        mode='lines+markers'
    ))
    
    fig_pareto.update_layout(
        yaxis2=dict(overlaying='y', side='right', range=[0, 110], ticksuffix='%'),
        yaxis=dict(title='Downtime (min)'),
        legend=dict(orientation='h')
    )
    
    st.plotly_chart(fig_pareto, use_container_width=True)

st.divider()

# ======================
# ROW 2 — MACHINE COMPARISON + SHIFT ANALYSIS
# ======================
col3, col4 = st.columns(2)

with col3:
    st.subheader("🏭 OEE by Machine")
    
    machine_oee = filtered_df.groupby('machine')[['oee','availability','performance','quality']].mean().reset_index()
    
    fig_machine = px.bar(
        machine_oee,
        x='machine',
        y='oee',
        color='oee',
        color_continuous_scale='RdYlGn',  # red = bad, green = good
        title='Average OEE per Machine',
        labels={'oee': 'OEE', 'machine': 'Machine'},
        text_auto='.1%'
    )
    
    fig_machine.add_hline(
        y=0.85,
        line_dash='dash',
        line_color='red',
        annotation_text='World Class (85%)'
    )
    
    fig_machine.update_layout(yaxis_tickformat='.0%')
    st.plotly_chart(fig_machine, use_container_width=True)

with col4:
    st.subheader("🔄 OEE by Shift")
    
    shift_oee = filtered_df.groupby('shift')[['oee','availability','performance','quality']].mean().reset_index()
    
    fig_shift = px.bar(
        shift_oee,
        x='shift',
        y=['availability', 'performance', 'quality'],
        title='Availability / Performance / Quality by Shift',
        labels={'value': 'Score', 'shift': 'Shift'},
        barmode='group',
        color_discrete_sequence=['#636EFA', '#EF553B', '#00CC96']
    )
    
    fig_shift.update_layout(yaxis_tickformat='.0%')
    st.plotly_chart(fig_shift, use_container_width=True)

st.divider()

# ======================
# ROW 3 — OEE GAUGE + RAW DATA TABLE
# ======================
col5, col6 = st.columns(2)

with col5:
    st.subheader("🎯 OEE Gauge")
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_oee * 100,
        delta={'reference': 85, 'suffix': '%'},
        title={'text': "Overall OEE %"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#00CC96"},
            'steps': [
                {'range': [0, 50], 'color': '#FF4444'},
                {'range': [50, 75], 'color': '#FFA500'},
                {'range': [75, 85], 'color': '#FFD700'},
                {'range': [85, 100], 'color': '#90EE90'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    
    st.plotly_chart(fig_gauge, use_container_width=True)

with col6:
    st.subheader("🗃️ Raw Data")
    
    # Show a clean summary table
    summary_table = filtered_df.groupby('machine').agg(
        Avg_OEE=('oee', 'mean'),
        Avg_Availability=('availability', 'mean'),
        Avg_Performance=('performance', 'mean'),
        Avg_Quality=('quality', 'mean'),
        Total_Downtime_min=('downtime_min', 'sum'),
        Total_Good_Parts=('good_parts', 'sum')
    ).round(3).reset_index()
    
    st.dataframe(summary_table, use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Filtered Data",
        data=csv,
        file_name='oee_filtered.csv',
        mime='text/csv'
    )