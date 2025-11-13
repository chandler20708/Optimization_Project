# International Coal Case Study – Scenario Testing Web App

This project is an **interactive optimization web application** built as part of the *Mathematical Programming and Optimization* coursework at Alliance Manchester Business School.  
It models and visualizes an **energy generation planning problem** for an international coal company, combining **profit maximization** with **environmental constraints** such as SO₂ and CO₂ emissions.

---

## Objective

The optimization model determines the **optimal fuel mix** (coal, biomass, stockpile, etc.) across multiple months and demand bands to:

- Maximize total profit (revenue – fuel cost – carbon cost – investment)
- Respect generation capacity, SO₂ bubble limit, and biomass share constraints
- Evaluate trade-offs under different **price and policy scenarios**

---

## Key Features

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

## Model Highlights

| Category | Description |
|-----------|--------------|
| **Decision Variables** | $x_{f, m, b}$: tons burned per fuel/month/band |
| **Objective** | $$\max Z = \sum_{m.b} \left[\left(p_{m,b} - 0.65 \right) * E_{m,b} + 45 * E_{m,b}^{bio} - \sum_f P_f * x_{f,m,b} - 15 * 0.86 * 0.8 * E_{m,b}\right]$$ |
| **Energy Generated** | $$E_{m,b} = \frac{\eta}{3.6} \sum_f \left( CV_f \, x_{f,m,b} \right)$$ |
| **Stockpile Inventory** | $$\sum_m \sum_b x_{\text{Stockpile},m,b} \le 600{,}000$$ |
| **Biomass Limit** | $$E_{m,b}^{bio} \leq 0.1 * E_{m,b}$$ |
| **Sulphur Emission** | $$S_{m,b} = \sum_f \left( x_{f,m,b} \, SO2_f \right)$$ |
| **Sulphur Bubble Limit** | $$\sum_m \sum_b S_{m,b} \leq 0.3 \times 30{,}000$$ |
| **Capacity Limit** | $$E_{m,b} \le 1000 \times H_{m,b}$$ |
| **No Coal (Summer Months)** | $$x_{\text{Colombian},m,b} = 0$$; $$x_{\text{Russian},m,b} = 0$$; $$x_{\text{Scottish},m,b} = 0$$ |
---

## Requirements

- **Python 3.11+**
- **Gurobi 11.0**
- **Polars / Pandas**
- **Plotly**
- **Streamlit**
- **NumPy / SciPy**

---

## How to Run Locally

```bash
# Clone repository
git clone https://github.com/chandler20708/Optimization_Project.git
cd Optimization_Project/international_coal

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

## Example Use Cases
- Compare profit vs. emissions trade-offs under different CO₂ price policies
- Evaluate FGD investment viability with varying SO₂ bubbles
- Identify binding constraints via shadow price heatmaps
- Visualize biomass share evolution over months and periods

⸻

## Acknowledgments
Developed by Chia-Te Liu (Chandler) as part of the Alliance Manchester Business School course project on Operational Research & Optimization.
Teammates: Flora, Karan, Minh, Prajna, Ansh.
Optimization solver powered by Gurobi Optimizer.

LinkedIn → [Chandler Liu](https://www.linkedin.com/in/chia-te-liu/)
