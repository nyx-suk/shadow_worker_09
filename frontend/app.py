import streamlit as st
import requests
import json
import time

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/api/v1/analyze-logs"

st.set_page_config(
    page_title="AI Shadow Worker (Lite)",
    page_icon="🤖",
    layout="wide"
)

# --- Header ---
st.title("AI Shadow Worker (Lite)")
st.markdown("Automate your repetitive tasks by analyzing your digital footprint.")

# --- Input Handling ---
with st.container():
    st.subheader("1. Provide Log Data")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload logs (.txt, .csv)", type=["txt", "csv"])
    
    # Text Area
    manual_input = st.text_area(
        "Or paste your logs here...",
        placeholder="User clicked Download, then opened Excel...",
        height=200
    )

    # Logic to determine input data
    log_data = ""
    if uploaded_file is not None:
        try:
            log_data = uploaded_file.read().decode("utf-8")
        except Exception as e:
            st.error(f"Failed to read file: {e}")
    else:
        log_data = manual_input

# --- API Integration & UI Update ---
if st.button("Analyze Logs", type="primary"):
    if not log_data.strip():
        st.warning("Please provide some log data before analyzing.")
    else:
        with st.spinner("Analyzing workflows..."):
            try:
                # Prepare Payload
                payload = {
                    "log_data": log_data,
                    "file_type": "text"
                }
                
                # Make POST Request
                response = requests.post(API_URL, json=payload, timeout=30)
                
                if response.status_code == 200:
                    res_json = response.json()
                    
                    if res_json.get("status") == "success" and res_json.get("data"):
                        data = res_json["data"]
                        primary_wf = data.get("primary_workflow")
                        
                        if primary_wf:
                            st.success("Analysis Complete!")
                            
                            # --- 5. State Mapping & 6. UI Update ---
                            # Metrics (Top Row)
                            m_col1, m_col2 = st.columns(2)
                            m_col1.metric("Confidence Score", f"{primary_wf.get('confidence_score', 0)}%")
                            m_col2.metric("Est. Time Saved", f"{primary_wf.get('estimated_time_saved_mins_per_week', 0)} mins/week")
                            
                            st.divider()
                            
                            # 2-Column Layout
                            c_left, c_right = st.columns([1, 1])
                            
                            with c_left:
                                st.subheader("💡 Automation Suggestion")
                                st.info(primary_wf.get("automation_suggestion", "No specific suggestion provided."))
                            
                            with c_right:
                                st.subheader("➡️ Workflow Steps")
                                steps = primary_wf.get("steps", [])
                                if steps:
                                    formatted_steps = " ➡️ ".join([f"**{step}**" for step in steps])
                                    st.write(formatted_steps)
                                else:
                                    st.write("No steps identified.")
                        else:
                            st.warning("No workflow detected")
                    else:
                        st.error(f"Analysis Failed: {res_json.get('message', 'Unknown Error')}")
                else:
                    st.error("Failed to analyze logs (Backend error)")
            
            except requests.exceptions.ConnectionError:
                st.error("Failed to analyze logs. Please ensure the backend is running at http://127.0.0.1:8000")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
