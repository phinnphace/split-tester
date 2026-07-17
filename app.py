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
st.caption(
    "Step right up, don't be shy. Pick a split, any split. "
    "Feeling shy? Stick with the same old 80/20. "
    "Feeling curious? Maybe even froggy? How about 60/40? "
    "Don't let me pressure you. You do you. Have a go, spin away."
)

wheel_html = """
<div style="text-align: center; background: #1a1a2e; padding: 20px; border-radius: 16px;">
  <canvas id="wheelCanvas" width="400" height="400" style="max-width: 100%;"></canvas>
  <br>
  <button onclick="spinWheel()" style="
    background: linear-gradient(135deg, #ff4b4b, #ff6b6b); 
    color: white; border: none; padding: 14px 50px;
    font-size: 20px; border-radius: 50px; cursor: pointer; 
    margin-top: 15px; font-weight: bold; letter-spacing: 1px;
    box-shadow: 0 4px 15px rgba(255,75,75,0.4);
  ">🎰 SPIN THE WHEEL</button>
  <div id="wheelResult" style="
    font-size: 24px; font-weight: bold; margin-top: 20px; 
    min-height: 40px; padding: 15px; border-radius: 12px;
  "></div>
</div>

<script>
const splits = [
  {label: "50/50", acc: "55.5%", color: "#FF6B6B"},
  {label: "60/40", acc: "64.8%", color: "#4ECDC4"},
  {label: "70/30", acc: "53.7%", color: "#45B7D1"},
  {label: "80/20", acc: "73.5%", color: "#96CEB4"},
  {label: "90/10", acc: "69.4%", color: "#FFD93D"},
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
  
  splits.forEach((s, i) => {
    const startAngle = rotation + i * sliceAngle;
    const endAngle = startAngle + sliceAngle;
    
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.closePath();
    ctx.fillStyle = s.color;
    ctx.fill();
    ctx.strokeStyle = '#1a1a2e';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(startAngle + sliceAngle / 2);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#1a1a2e';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText(s.label, radius * 0.55, 4);
    ctx.restore();
  });
  
  // Center hub
  const grad = ctx.createRadialGradient(cx, cy, 5, cx, cy, 30);
  grad.addColorStop(0, '#fff');
  grad.addColorStop(1, '#ddd');
  ctx.beginPath();
  ctx.arc(cx, cy, 28, 0, 2 * Math.PI);
  ctx.fillStyle = grad;
  ctx.fill();
  ctx.strokeStyle = '#1a1a2e';
  ctx.lineWidth = 3;
  ctx.stroke();
  
  // Pointer
  ctx.beginPath();
  ctx.moveTo(cx + radius + 8, cy);
  ctx.lineTo(cx + radius - 20, cy - 18);
  ctx.lineTo(cx + radius - 20, cy + 18);
  ctx.closePath();
  ctx.fillStyle = '#fff';
  ctx.fill();
  ctx.strokeStyle = '#1a1a2e';
  ctx.lineWidth = 2;
  ctx.stroke();
}

function getSelectedSlice(rotation) {
  const sliceAngle = (2 * Math.PI) / splits.length;
  let normalized = ((rotation % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  const selected = Math.floor(normalized / sliceAngle);
  return splits[(splits.length - selected) % splits.length];
}

function spinWheel() {
  if (spinning) return;
  spinning = true;
  result.innerHTML = "";
  result.style.background = "transparent";
  
  const spins = 5 + Math.random() * 5;
  const totalRotation = spins * 2 * Math.PI + Math.random() * 2 * Math.PI;
  const duration = 3000;
  const startTime = Date.now();
  const startAngle = angle;
  
  function animate() {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    angle = startAngle + totalRotation * eased;
    drawWheel(angle);
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      spinning = false;
      const selected = getSelectedSlice(angle);
      result.innerHTML = "🎉 " + selected.label + " split — <b>" + selected.acc + " accuracy</b>";
      result.style.background = "linear-gradient(135deg, " + selected.color + "33, " + selected.color + "11)";
      result.style.color = "#fff";
    }
  }
  
  animate();
}

drawWheel(0);
</script>
"""

st.components.v1.html(wheel_html, height=560, scrolling=False)
