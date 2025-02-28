# app.py
import streamlit as st
import time
from services.live_stream_service import VideoProcessor


# Create processor instance
if "processor" not in st.session_state:
    st.session_state.processor = VideoProcessor()

# Streamlit UI
st.set_page_config(page_title="Dog Behavior Analyzer", layout="wide")
st.title("🐶 Real-Time Dog Behavior Analysis")

# Control Panel
with st.sidebar:
    st.header("Controls")
    source_type = st.radio("Input Source", ["RTSP", "File"])
    
    if source_type == "RTSP":
        rtsp_url = st.text_input("RTSP URL", "rtsp://example.com/stream")
        source = rtsp_url
    else:
        uploaded_file = st.file_uploader("Upload Video", type=["mp4", "avi"])
        source = "data/uploaded.mp4" if uploaded_file else None
        if uploaded_file:
            with open(source, "wb") as f:
                f.write(uploaded_file.getbuffer())
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Start"):
            if source:
                st.session_state.processor.start_stream(source)
    with col2:
        if st.button("⏹ Stop"):
            st.session_state.processor.stop_stream()

# Main Display
col1, col2 = st.columns([3, 1])

with col1:
    st.header("Live Feed")
    video_placeholder = st.empty()
    classification_placeholder = st.empty()  # Placeholder for classification value
    
    # Display video frames and classification value
    if st.session_state.processor.running:
        while st.session_state.processor.running:
            frame, classification = st.session_state.processor.get_latest_frame()  # Update method to return classification
            if frame is not None:
                video_placeholder.image(frame, channels="RGB")
                classification_placeholder.markdown(f"**Classification:** {classification}")  # Show classification under stream
            time.sleep(1/30)  # Match capture rate
    else:
        video_placeholder.text("Stream stopped - Click Start to begin")
        classification_placeholder.text("")

with col2:
    st.header("Status")
    if st.session_state.processor.running:
        st.success("✅ System Active")
        st.metric("Frames Captured", st.session_state.processor.frame_count)
        st.metric("Last Processed", 
                st.session_state.processor.last_processed.strftime("%H:%M:%S") 
                if st.session_state.processor.last_processed else "N/A")
    else:
        st.warning("⏸ System Idle")

# Cleanup on exit
def cleanup():
    st.session_state.processor.stop_stream()

import atexit
atexit.register(cleanup)