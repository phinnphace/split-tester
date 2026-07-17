#!/usr/bin/env python3
"""
Split Ratio Demo
Drop-in app that tests how train/val split ratio affects model performance.
Uses real Chinese character images from the CASIA handwriting database.
"""
import streamlit as st
import zipfile
import io
import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import matplotlib.pyplot as plt

st.set_page_config(page_title="Split Ratio Tester", layout="wide")
st.title("Does Your 80/20 Split Matter?")
st.caption("Same model. Same seed. Same data. Only the split changes.")

# ============================================================
# LOAD SAMPLE DATA
# ============================================================
@st.cache_data
def load_sample_data():
    """Extract images from the bundled zip file."""
    images = []
    labels = []
    
    with zipfile.ZipFile('sample_data.zip', 'r') as z:
        for fname in z.namelist():
            if fname.endswith('.png'):
                # Parse label from path: condition_a/da/da_0001.png -> 1
                label = 1 if '/da/' in fname else 0
                with z.open(fname) as f:
                    img = Image.open(f).convert('L')
                    img = img.resize((32, 32))  # Small for fast demo
                    images.append(np.array(img).flatten())
                    labels.append(label)
    
    return np.array(images), np.array(labels)

X, y = load_sample_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("Settings")
model_name = st.sidebar.selectbox(
    "Model",
    ["Random Forest", "Neural Network (MLP)"]
)
seed = st.sidebar.number_input("Random Seed", value=42, step=1)
show_raw = st.sidebar.checkbox("Show raw numbers", value=True)

# ============================================================
# RUN SPLIT TEST
# ============================================================
st.header("Split Ratio Test")
st.caption(f"Running on {len(X)} real Chinese character images ({sum(y)} positive, {len(y)-sum(y)} negative)")

if st.button("Run Test", type="primary") or 'results' in st.session_state:
    
    if 'results' not in st.session_state or st.button("Rerun"):
        splits = [0.5, 0.6, 0.7, 0.8, 0.9]
        results = {}
        
        progress = st.progress(0)
        status = st.empty()
        
        rng = np.random.RandomState(seed)
        n = len(X)
        
        for i, split in enumerate(splits):
            status.text(f"Testing {split:.0%}/{(1-split):.0%} split...")
            
            # Fixed shuffle
            indices = rng.permutation(n)
            split_idx = int(n * split)
            train_idx = indices[:split_idx]
            val_idx = indices[split_idx:]
            
            # Build model
            if model_name == "Random Forest":
                model = RandomForestClassifier(n_estimators=100, random_state=seed)
            else:
                model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=seed)
            
            # Train
            model.fit(X[train_idx], y[train_idx])
            
            # Evaluate
            preds = model.predict(X[val_idx])
            acc = (preds == y[val_idx]).mean()
            
            label = f"{split:.0%}/{(1-split):.0%}"
            results[label] = {
                'accuracy': acc,
                'train_size': len(train_idx),
                'val_size': len(val_idx)
            }
            
            progress.progress((i + 1) / len(splits))
        
        status.text("Done!")
        st.session_state.results = results
        st.session_state.model_name = model_name
    
    # ============================================================
    # RESULTS
    # ============================================================
    results = st.session_state.results
    splits = list(results.keys())
    accs = [results[s]['accuracy'] for s in splits]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Accuracy", f"{max(accs):.1%}", delta=f"at {splits[accs.index(max(accs))]}")
    with col2:
        st.metric("Worst Accuracy", f"{min(accs):.1%}", delta=f"at {splits[accs.index(min(accs))]}")
    with col3:
        spread = max(accs) - min(accs)
        st.metric("Spread", f"{spread:.1%}", delta="points across splits")
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(splits))
    ax.plot(x, [r['accuracy'] for r in results.values()], 'o-', 
            color='#1f77b4', linewidth=2, markersize=10)
    ax.axhline(y=np.mean(accs), color='gray', linestyle='--', alpha=0.5, label='Mean')
    ax.set_xticks(x)
    ax.set_xticklabels(splits)
    ax.set_ylabel('Validation Accuracy')
    ax.set_xlabel('Train/Val Split Ratio')
    ax.set_title(f'Effect of Split Ratio on {model_name}')
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)
    
    # Raw numbers
    if show_raw:
        st.subheader("Raw Results")
        for split, data in results.items():
            st.write(f"**{split}**: {data['accuracy']:.1%} (train={data['train_size']}, val={data['val_size']})")
    
    # Interpretation
    st.divider()
    st.subheader("What This Means")
    
    if spread > 0.10:
        st.warning(f"""
        Your model's validation accuracy varies by **{spread:.0%}** just from changing the split ratio.
        
        If you'd stopped at **{splits[accs.index(min(accs))]}**, you'd report **{min(accs):.1%}**.
        At **{splits[accs.index(max(accs))]}**, you'd report **{max(accs):.1%}**.
        
        Both are "correct." Neither tells the full story. Your 80/20 default deserves scrutiny.
        """)
    elif spread > 0.03:
        st.info(f"""
        Moderate variation ({spread:.0%}) across splits. Your 80/20 default is probably fine,
        but it's worth reporting the range in any publication.
        """)
    else:
        st.success(f"""
        Very stable across splits (only {spread:.0%} variation). Your model is robust
        to split ratio. Carry on with 80/20.
        """)
# ============================================================
# WHEEL OF SPLITS
# ============================================================
st.header("🎰 Wheel of Splits")
st.caption("Spin the wheel. Whatever split it lands on — that's your result. Publish it. Defend it. That's what the 80/20 default does.")

wheel_html = """
<div style="text-align: center;">
  <canvas id="wheelCanvas" width="400" height="400" style="max-width: 100%;"></canvas>
  <br>
  <button onclick="spinWheel()" style="
    background: #ff4b4b; color: white; border: none; padding: 12px 40px;
    font-size: 18px; border-radius: 8px; cursor: pointer; margin-top: 10px;
  ">🎰 SPIN THE WHEEL</button>
  <div id="wheelResult" style="
    font-size: 28px; font-weight: bold; margin-top: 20px; min-height: 40px;
  "></div>
</div>

<script>
const splits = [
  {label: "50/50\\n55.5%", color: "#FF6B6B"},
  {label: "60/40\\n64.8%", color: "#4ECDC4"},
  {label: "70/30\\n53.7%", color: "#45B7D1"},
  {label: "80/20\\n73.5%", color: "#96CEB4"},
  {label: "90/10\\n69.4%", color: "#FFEAA7"},
];

const canvas = document.getElementById('wheelCanvas');
const ctx = canvas.getContext('2d');
const result = document.getElementById('wheelResult');
let spinning = false;
let angle = 0;

function drawWheel(rotation) {
  const cx = 200, cy = 200, radius = 180;
  const sliceAngle = (2 * Math.PI) / splits.length;
  
  ctx.clearRect(0, 0, 400, 400);
  
  // Draw slices
  splits.forEach((s, i) => {
    const startAngle = rotation + i * sliceAngle;
    const endAngle = startAngle + sliceAngle;
    
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.closePath();
    ctx.fillStyle = s.color;
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Label
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(startAngle + sliceAngle / 2);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#333';
    ctx.font = 'bold 14px sans-serif';
    const lines = s.label.split('\\n');
    lines.forEach((line, j) => {
      ctx.fillText(line, radius * 0.6, (j - 0.5) * 20);
    });
    ctx.restore();
  });
  
  // Center circle + pointer
  ctx.beginPath();
  ctx.arc(cx, cy, 25, 0, 2 * Math.PI);
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.strokeStyle = '#333';
  ctx.lineWidth = 3;
  ctx.stroke();
  
  // Pointer triangle
  ctx.beginPath();
  ctx.moveTo(cx + radius + 10, cy);
  ctx.lineTo(cx + radius - 15, cy - 15);
  ctx.lineTo(cx + radius - 15, cy + 15);
  ctx.closePath();
  ctx.fillStyle = '#333';
  ctx.fill();
}

function getSelectedSlice(rotation) {
  const sliceAngle = (2 * Math.PI) / splits.length;
  const pointerAngle = 0; // points right
  let normalized = ((rotation % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  const selected = Math.floor(normalized / sliceAngle);
  return splits[(splits.length - selected) % splits.length];
}

function spinWheel() {
  if (spinning) return;
  spinning = true;
  result.innerHTML = "";
  
  const spins = 5 + Math.random() * 5;
  const totalRotation = spins * 2 * Math.PI + Math.random() * 2 * Math.PI;
  const duration = 3000;
  const startTime = Date.now();
  const startAngle = angle;
  
  function animate() {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out
    const eased = 1 - Math.pow(1 - progress, 3);
    angle = startAngle + totalRotation * eased;
    drawWheel(angle);
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      spinning = false;
      const selected = getSelectedSlice(angle);
      result.innerHTML = "🎉 " + selected.label.replace('\\n', ' — ') + " accuracy!";
    }
  }
  
  animate();
}

drawWheel(0);
</script>
"""

st.components.v1.html(wheel_html, height=550)

# ============================================================
# ABOUT
# ============================================================
st.divider()
st.caption(
    "This demo uses real handwritten Chinese characters from the CASIA-HWDB database "
    "(Liu et al., 2011). It emerged from a side quest in a larger experiment on "
    "contextual visual learning. [Full project](https://github.com/phinnphace/80-20) | "
    "[Interactive dashboard](https://80-20.streamlit.app)"
)