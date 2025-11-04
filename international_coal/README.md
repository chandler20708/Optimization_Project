# 🌍 International Coal Case Study – Optimization Web App

This project is an **interactive optimization web application** built as part of the *Mathematical Programming and Optimization* coursework at Alliance Manchester Business School.  
It models and visualizes an **energy generation planning problem** for an international coal company, combining **profit maximization** with **environmental constraints** such as SO₂ and CO₂ emissions.

---

## 🎯 Objective

The optimization model determines the **optimal fuel mix** (coal, biomass, stockpile, etc.) across multiple months and demand bands to:

- Maximize total profit (revenue – fuel cost – carbon cost – investment)
- Respect generation capacity, SO₂ bubble limit, and biomass share constraints
- Evaluate trade-offs under different **price and policy scenarios**

---

## 🧩 Key Features

- **Gurobi-based LP/MILP model**  
  Includes decision variables for fuel mix, emission levels, and FGD investment.
- **Scenario and sensitivity analysis**  
  Test how changes in electricity price, fuel cost, or emission price affect profit and fuel decisions.
- **Streamlit web app interface**  
  Allows users to adjust parameters, run optimization, and visualize results interactively.
- **Dynamic visualizations**  
  - Fuel mix bar chart (by month/band)  
  - Profit comparison across scenarios  
  - Constraint binding heatmaps  
  - Biomass share and emission composition plots
- **Experiment logging**  
  Stores model inputs and outputs in session state for later analysis.

---

## 🧮 Model Highlights

| Category | Description |
|-----------|--------------|
| **Decision Variables** | `x[fuel, month, band]`: tons burned per fuel/month/band; binary FGD investment variable |
| **Objective** | See mathematical form below |
| **Constraints** | Energy balance, capacity, biomass ≤ 10%, SO₂ bubble, FGD efficiency, and emission limits |

**Objective function:**
max Z = Σ_m Σ_b [(price[m,b] - 0.65)*energy[m,b] + ROC*energy[Biomass,m,b]
          - Σ_f fuel_cost[f]*x[f,m,b]
          - CO2_price*exchange_rate*0.8*energy[m,b]
          - SO2_reduced[m,b]*SO2_price] - FGD_cost

---

## 🧰 Tech Stack

- **Python 3.11+**
- **Gurobi 11.0**
- **Polars / Pandas**
- **Plotly**
- **Streamlit**
- **NumPy / SciPy**

---

## 🚀 How to Run Locally

```bash
# Clone repository
git clone https://github.com/chandler20708/Optimization_Project.git
cd Optimization_Project/international_coal

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

## 📊 Example Use Cases
- Compare profit vs. emissions trade-offs under different CO₂ price policies
- Evaluate FGD investment viability with varying SO₂ bubbles
- Identify binding constraints via shadow price heatmaps
- Visualize biomass share evolution over months and periods

⸻

## 📖 Acknowledgments

Developed by Chia-Te Liu (Chandler) as part of the Alliance Manchester Business School course project on Operational Research & Optimization.
Supervisors and teammates: Flora, Karan, Minh.
Optimization solver powered by Gurobi Optimizer.

LinkedIn → linkedin.com/in/chia-te-liu
