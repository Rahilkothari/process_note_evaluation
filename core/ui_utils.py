import streamlit as st

@st.cache_data
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@500;600;700&display=swap');

        /* Hide Streamlit Branding completely */
        #MainMenu {visibility: hidden;}
        header[data-testid="stHeader"] {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {visibility: hidden;}

        /* Brand Logo at Top Left in Sidebar Header */
        [data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            display: flex;
            padding: 16px 16px 6px 16px;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarHeader"] img {
            max-height: 48px;
            width: auto;
        }
        
        /* Global Typography */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
            color: #1E293B;
        }
        
        code, pre, .stCodeBlock {
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        /* Soften the main app background */
        .stApp {
            background-color: #FAFAFA;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
            box-shadow: 2px 0 12px rgba(0,0,0,0.03);
        }
        [data-testid="stSidebarNav"] span {
            font-weight: 500;
            font-size: 14px;
            color: #475569;
            text-transform: capitalize;
        }
        
        /* Headers with Display Font */
        h1 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #0F172A;
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        h2 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            color: #1E293B;
            letter-spacing: -0.02em;
            font-size: 1.75rem !important;
        }
        h3 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            color: #1E293B;
            letter-spacing: -0.01em;
            font-size: 1.25rem !important;
        }
        h4, h5 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: #334155;
        }
        
        /* Container/Form styling (Premium Elevation) */
        [data-testid="stForm"], .stContainer {
            background-color: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #F1F5F9;
            transition: box-shadow 0.2s ease;
        }
        [data-testid="stForm"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
            border-color: #E2E8F0;
        }
        [data-testid="stForm"] {
            padding: 32px;
            margin-bottom: 24px;
        }

        /* Distinct AI Expander Drawer Styling (Gradient Card with Violet/Indigo Accents) */
        [data-testid="stExpander"] {
            background: linear-gradient(135deg, #FAF5FF 0%, #EEF2FF 50%, #F5F3FF 100%) !important;
            border-radius: 14px !important;
            border: 1.5px solid #C7D2FE !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.10) !important;
            margin: 12px 0 18px 0 !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
        }
        [data-testid="stExpander"]:hover {
            border-color: #818CF8 !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.20) !important;
        }
        [data-testid="stExpander"] details {
            border: none !important;
        }
        [data-testid="stExpander"] details summary {
            background-color: transparent !important;
            padding: 13px 18px !important;
            border-radius: 12px !important;
            cursor: pointer !important;
            transition: background-color 0.2s ease !important;
        }
        [data-testid="stExpander"] details summary:hover {
            background-color: rgba(224, 231, 255, 0.5) !important;
        }
        [data-testid="stExpander"] details summary p {
            font-size: 14.5px !important;
            font-weight: 700 !important;
            color: #4338CA !important;
            letter-spacing: -0.01em !important;
        }
        [data-testid="stExpander"] details summary svg {
            color: #6366F1 !important;
            transform: scale(1.1);
            filter: drop-shadow(0 1px 2px rgba(99, 102, 241, 0.3));
        }
        [data-testid="stExpander"] details[open] {
            border-color: #6366F1 !important;
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15) !important;
        }
        [data-testid="stExpander"] details[open] summary {
            border-bottom: 1px solid #E0E7FF !important;
            background-color: rgba(238, 242, 255, 0.85) !important;
        }
        [data-testid="stExpander"] details > div:last-child {
            padding: 18px 22px !important;
            background-color: #FFFFFF !important;
        }
        
        /* Input field styling */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            transition: all 0.2s ease;
            padding: 12px 14px;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: #1E293B;
            background-color: #FFFFFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset;
        }
        .stSelectbox>div>div>div {
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            transition: all 0.2s ease;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: #1E293B;
            background-color: #FFFFFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset;
        }
        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stSelectbox>div>div>div:focus {
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
        }
        
        /* Metrics Styling */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        [data-testid="stMetricLabel"] {
            color: #64748B;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stMetricValue"] {
            color: #0F172A;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 32px;
            margin-top: 4px;
        }
        
        /* Tab Styling - Sleek horizontal pills */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            padding-bottom: 12px;
            border-bottom: 1px solid #E2E8F0;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            background-color: transparent;
            border: none;
            color: #64748B;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #F1F5F9;
            color: #334155;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #E2E8F0 !important;
            color: #0F172A !important;
            font-weight: 600;
        }
        
        /* Buttons */
        .stButton>button {
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            padding: 8px 20px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #E2E8F0;
            background-color: #FFFFFF;
            color: #1E293B;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .stButton>button:hover {
            background-color: #F8FAFC;
            border-color: #CBD5E1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Primary Buttons */
        .stButton>button[kind="primary"] {
            background-color: #4F46E5;
            color: #FFFFFF;
            border-color: #4F46E5;
            box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3);
        }
        .stButton>button[kind="primary"]:hover {
            background-color: #4338CA;
            border-color: #4338CA;
            box-shadow: 0 4px 6px rgba(79, 70, 229, 0.4);
        }
        
        /* Status Colors / Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 16px;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            line-height: 1;
        }
        .badge-pass { color: #047857; background: #D1FAE5; border: 1px solid #10B981; }
        .badge-warning { color: #B45309; background: #FEF3C7; border: 1px solid #F59E0B; }
        .badge-fail { color: #B91C1C; background: #FEE2E2; border: 1px solid #EF4444; }
        .badge-draft { color: #475569; background: #F1F5F9; border: 1px solid #CBD5E1; }
        .badge-review { color: #4338CA; background: #E0E7FF; border: 1px solid #818CF8; }
        
        /* DataFrame/Table styling enhancements */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            overflow: hidden;
        }
        
        /* Custom progress bar wrapper */
        .score-bar-container {
            width: 100%;
            background-color: #F1F5F9;
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
            margin-top: 8px;
        }
        .score-bar-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 0.5s ease-out;
        }
        .score-pass { background-color: #10B981; }
        .score-warn { background-color: #F59E0B; }
        .score-fail { background-color: #EF4444; }
        
        /* Expander Enhancements */
        [data-testid="stExpander"] {
            border-radius: 10px !important;
            border: 1.5px solid #C7D2FE !important;
            background: #FFFFFF !important;
            box-shadow: 0 1px 3px rgba(99, 102, 241, 0.08) !important;
            margin-bottom: 16px !important;
        }
        [data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #3730A3 !important;
            padding: 10px 14px !important;
        }
        
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=3600)
def get_mermaid_png_bytes(clean_code: str) -> bytes:
    """Fetches high-resolution PNG bytes for Mermaid flowchart via mermaid.ink service."""
    try:
        import base64
        import urllib.request
        clean_code = str(clean_code).replace("&amp;", "&")
        b64 = base64.b64encode(clean_code.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{b64}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5) as res:
            if res.status == 200:
                return res.read()
    except Exception:
        pass
    return None


@st.cache_data(show_spinner=False, ttl=3600)
def get_mermaid_svg_bytes(clean_code: str) -> bytes:
    """Fetches vector SVG bytes for Mermaid flowchart via mermaid.ink service."""
    try:
        import base64
        import urllib.request
        clean_code = str(clean_code).replace("&amp;", "&")
        b64 = base64.b64encode(clean_code.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/svg/{b64}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5) as res:
            if res.status == 200:
                return res.read()
    except Exception:
        pass
    return None


def render_mermaid_flowchart(chart_code: str, height: int = None, show_code_toggle: bool = False):
    """
    Renders Mermaid flowchart code as a high-fidelity visual SVG diagram with
    clean rectangular process boxes, decision diamonds, and labeled connection arrows,
    along with direct SVG and PNG download options.
    """
    import streamlit.components.v1 as components

    if not chart_code or not str(chart_code).strip():
        st.info("No flowchart diagram data available.")
        return

    clean_code = str(chart_code).replace("```mermaid", "").replace("```", "").strip()
    while "&amp;" in clean_code:
        clean_code = clean_code.replace("&amp;", "&")
    
    # Calculate responsive container height based on node count
    lines = [l for l in clean_code.split("\n") if l.strip()]
    calc_height = max(420, min(880, len(lines) * 45 + 110)) if not height else height

    if show_code_toggle:
        dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
        with dl_col1:
            png_bytes = get_mermaid_png_bytes(clean_code)
            if png_bytes:
                st.download_button(
                    "🖼️ Download PNG Image",
                    data=png_bytes,
                    file_name="process_flowchart.png",
                    mime="image/png",
                    use_container_width=True,
                    help="Click to download a high-resolution PNG image directly."
                )
            else:
                st.button("🖼️ PNG Image (Download in card)", disabled=True, use_container_width=True)
        with dl_col2:
            svg_bytes = get_mermaid_svg_bytes(clean_code)
            if svg_bytes:
                st.download_button(
                    "📥 Download Vector SVG",
                    data=svg_bytes,
                    file_name="process_flowchart.svg",
                    mime="image/svg+xml",
                    use_container_width=True,
                    help="Click to download crystal-clear vector SVG for printing or docs."
                )
            else:
                st.button("📥 Vector SVG (Download in card)", disabled=True, use_container_width=True)
        with dl_col3:
            st.download_button(
                "📄 Download Mermaid (.mmd)",
                data=clean_code,
                file_name="process_flowchart.mmd",
                mime="text/plain",
                use_container_width=True,
                help="Download raw Mermaid diagram code."
            )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
      <style>
        * {{
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }}
        body {{
          background-color: #FFFFFF;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 14px;
          min-height: 100%;
        }}
        .diagram-card {{
          width: 100%;
          background: #FFFFFF;
          border: 1.5px solid #E2E8F0;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.04);
          display: flex;
          flex-direction: column;
          overflow-x: auto;
        }}
        .card-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;
          padding-bottom: 10px;
          border-bottom: 1px solid #F1F5F9;
        }}
        .btn-dl {{
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          font-size: 12px;
          font-weight: 600;
          color: #4338CA;
          background: #EEF2FF;
          border: 1px solid #C7D2FE;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s ease;
        }}
        .btn-dl:hover {{
          background: #E0E7FF;
          border-color: #A5B4FC;
        }}
        .btn-png {{
          color: #0F172A;
          background: #F8FAFC;
          border-color: #CBD5E1;
        }}
        .btn-png:hover {{
          background: #F1F5F9;
          border-color: #94A3B8;
        }}
        .mermaid {{
          display: flex;
          justify-content: center;
          width: 100%;
          text-align: center;
        }}
        .mermaid svg {{
          max-width: 100% !important;
          height: auto !important;
          filter: drop-shadow(0 2px 5px rgba(0,0,0,0.06));
        }}
        #error-msg {{
          display: none;
          color: #DC2626;
          font-size: 13px;
          padding: 12px;
          background: #FEF2F2;
          border-radius: 6px;
        }}
      </style>
    </head>
    <body>
      <div class="diagram-card">
        <div class="card-header">
          <span style="font-size: 13px; font-weight: 700; color: #334155;">📊 Interactive Process Flowchart</span>
          <div style="display: flex; gap: 8px;">
            <button onclick="downloadSVG()" class="btn-dl" title="Save high-resolution vector SVG">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download SVG
            </button>
            <button onclick="downloadPNG()" class="btn-dl btn-png" title="Save PNG image file">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              Download PNG
            </button>
          </div>
        </div>
        <div id="error-msg"></div>
        <pre class="mermaid" id="mermaid-target">
{clean_code}
        </pre>
      </div>

      <script>
        function sanitizeDiagramText() {{
          try {{
            var svg = document.querySelector('.mermaid svg');
            if (!svg) return;
            
            var walker = document.createTreeWalker(svg, NodeFilter.SHOW_TEXT, null, false);
            var node;
            while ((node = walker.nextNode())) {{
              if (node.nodeValue && node.nodeValue.indexOf('&amp;') !== -1) {{
                node.nodeValue = node.nodeValue.replace(/&amp;/g, '&');
              }}
            }}

            var els = svg.querySelectorAll('text, tspan, foreignObject, span, div, p');
            for (var i = 0; i < els.length; i++) {{
              var el = els[i];
              if (el.children.length === 0 && el.textContent && el.textContent.indexOf('&amp;') !== -1) {{
                el.textContent = el.textContent.replace(/&amp;/g, '&');
              }}
            }}
          }} catch(e) {{}}
        }}

        function downloadSVG() {{
          try {{
            sanitizeDiagramText();
            var svg = document.querySelector('.mermaid svg');
            if (!svg) {{ alert('Diagram is still rendering, please wait a moment.'); return; }}
            var clone = svg.cloneNode(true);
            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            var svgData = new XMLSerializer().serializeToString(clone);
            svgData = svgData.replace(/&amp;amp;/g, '&amp;');
            var svgBlob = new Blob([svgData], {{ type: 'image/svg+xml;charset=utf-8' }});
            var url = URL.createObjectURL(svgBlob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'process_flowchart.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(function() {{ URL.revokeObjectURL(url); }}, 200);
          }} catch(e) {{
            alert('Please use the Download Vector SVG button above the diagram.');
          }}
        }}

        function downloadPNG() {{
          try {{
            sanitizeDiagramText();
            var svg = document.querySelector('.mermaid svg');
            if (!svg) {{ alert('Diagram is still rendering, please wait a moment.'); return; }}
            var clone = svg.cloneNode(true);
            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            var svgData = new XMLSerializer().serializeToString(clone);
            svgData = svgData.replace(/&amp;amp;/g, '&amp;');
            var DOMURL = window.URL || window.webkitURL || window;
            var svgUrl = DOMURL.createObjectURL(svgBlob);
            var img = new Image();
            img.onload = function() {{
              try {{
                var bbox = svg.getBoundingClientRect();
                var scale = 2;
                var width = Math.max(bbox.width || 800, 600) * scale;
                var height = Math.max(bbox.height || 600, 400) * scale;
                var canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                var ctx = canvas.getContext('2d');
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(0, 0, width, height);
                ctx.drawImage(img, 0, 0, width, height);
                DOMURL.revokeObjectURL(svgUrl);

                if (canvas.toBlob) {{
                  canvas.toBlob(function(blob) {{
                    if (blob) {{
                      var dlUrl = DOMURL.createObjectURL(blob);
                      var a = document.createElement('a');
                      a.href = dlUrl;
                      a.download = 'process_flowchart.png';
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      setTimeout(function() {{ DOMURL.revokeObjectURL(dlUrl); }}, 500);
                    }} else {{
                      var pngUrl = canvas.toDataURL('image/png');
                      var a = document.createElement('a');
                      a.href = pngUrl;
                      a.download = 'process_flowchart.png';
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                    }}
                  }}, 'image/png');
                }} else {{
                  var pngUrl = canvas.toDataURL('image/png');
                  var a = document.createElement('a');
                  a.href = pngUrl;
                  a.download = 'process_flowchart.png';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }}
              }} catch(err) {{
                alert('Browser blocked local export. Please click the \"Download PNG Image\" button above the diagram.');
              }}
            }};
            img.onerror = function() {{
              alert('Could not convert SVG to image locally. Please use the \"Download PNG Image\" button directly above the diagram.');
            }};
            img.src = svgUrl;
          }} catch(e) {{
            alert('Please use the \"Download PNG Image\" button directly above the diagram.');
          }}
        }}

        try {{
          var targetEl = document.getElementById('mermaid-target');
          if (targetEl) {{
            while (targetEl.textContent.indexOf('&amp;') !== -1) {{
              targetEl.textContent = targetEl.textContent.replace(/&amp;/g, '&');
            }}
          }}

          mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
              useMaxWidth: true,
              htmlLabels: false,
              curve: 'basis'
            }},
            themeVariables: {{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              fontSize: '13.5px',
              primaryColor: '#EEF2FF',
              primaryTextColor: '#1E293B',
              primaryBorderColor: '#6366F1',
              lineColor: '#64748B',
              secondaryColor: '#ECFDF5',
              tertiaryColor: '#FEF3C7',
              mainBkg: '#FFFFFF'
            }}
          }});

          try {{
            var observer = new MutationObserver(function() {{
              sanitizeDiagramText();
            }});
            var card = document.querySelector('.diagram-card');
            if (card) {{
              observer.observe(card, {{ childList: true, subtree: true, characterData: true }});
            }}
          }} catch(e) {{}}

          setTimeout(sanitizeDiagramText, 40);
          setTimeout(sanitizeDiagramText, 120);
          setTimeout(sanitizeDiagramText, 300);
          setTimeout(sanitizeDiagramText, 700);
          setTimeout(sanitizeDiagramText, 1500);
        }} catch(err) {{
          var el = document.getElementById('error-msg');
          if (el) {{
            el.style.display = 'block';
            el.innerText = 'Unable to render diagram visually: ' + err.message;
          }}
        }}
      </script>
    </body>
    </html>
    """

    components.html(html_content, height=calc_height, scrolling=True)

    if show_code_toggle:
        with st.expander("📝 View / Copy Raw Mermaid Syntax", expanded=False):
            st.code(clean_code, language="mermaid")

