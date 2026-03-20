
import sys
print(f"Python version: {sys.version}")

print("Testing Professional Stack Imports...")
try:
    import streamlit as st
    print("- streamlit imported")
    import pandas as pd
    print("- pandas imported")
    import plotly.graph_objects as go
    print("- plotly imported")
    import PyPDF2
    print("- PyPDF2 imported")
    import google.generativeai as genai
    print("- google-generativeai imported")
    import pymongo
    print("- pymongo imported")
    import reportlab
    print("- reportlab imported")
    print("All professional stack imports SUCCESSFUL.")
except Exception as e:
    print(f"FAILED: {e}")
