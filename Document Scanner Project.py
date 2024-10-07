import streamlit as st
import io
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    return ", ".join(["[{:.2f}, {:.2f}]".format(p.x, p.y) for p in bounding_box])

def analyze_document(endpoint, key, file_content=None, file_url=None):
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    if file_content:
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-read", file_content
        )
    elif file_url:
        poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-read", file_url
        )
    else:
        raise ValueError("Either file content or URL must be provided")

    result = poller.result()
    return result

st.title("Document Analyzer")

endpoint = st.text_input("Enter Azure Form Recognizer Endpoint:")
key = st.text_input("Enter Azure Form Recognizer Key:", type="password")

input_method = st.radio("Choose input method:", ("File Upload", "URL"))

if input_method == "File Upload":
    uploaded_file = st.file_uploader("Choose a document file", type=["png", "jpg", "jpeg", "pdf"])
else:
    file_url = st.text_input("Enter Document URL:")

if st.button("Analyze Document"):
    if endpoint and key:
        with st.spinner("Analyzing document..."):
            try:
                if input_method == "File Upload" and uploaded_file is not None:
                    file_content = uploaded_file.read()
                    result = analyze_document(endpoint, key, file_content=file_content)
                elif input_method == "URL" and file_url:
                    result = analyze_document(endpoint, key, file_url=file_url)
                else:
                    st.warning("Please provide a document file or URL.")
                    st.stop()

                st.subheader("Document Content:")
                st.text(result.content)

                st.subheader("Document Styles:")
                for idx, style in enumerate(result.styles):
                    st.write(f"Style {idx + 1}: {'Handwritten' if style.is_handwritten else 'Not handwritten'}")

                st.subheader("Page Analysis:")
                for page in result.pages:
                    st.write(f"Page {page.page_number}:")
                    st.write(f"- Dimensions: {page.width} x {page.height} {page.unit}")
                    
                    st.write("Lines:")
                    for line_idx, line in enumerate(page.lines):
                        st.write(f"  - Line {line_idx + 1}: '{line.content}'")
                        st.write(f"    Bounding Box: {format_bounding_box(line.polygon)}")
                    
                    st.write("Words:")
                    for word in page.words:
                        st.write(f"  - '{word.content}' (Confidence: {word.confidence:.2f})")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please fill in the Azure Form Recognizer Endpoint and Key fields.")