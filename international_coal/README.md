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
| **Decision Variables** | `x[fuel, month, band]`: tons burned per fuel/month/band; binary FGD investment variable |
| **Objective** | ![Objective Function](https://latex.codecogs.com/png.latex?%5Cbg_white%20%5Cmax%20Z%20%3D%20%5Csum_%7Bm%20%5Cin%20Months%7D%20%5Csum_%7Bb%20%5Cin%20Bands%7D%20%5CBigg%5B%28price_%7Bm%2Cb%7D-0.65%29%5Ccdot%20energy_%7Bm%2Cb%7D%2BROC%5Ccdot%20energy_%7BBiomass%2Cm%2Cb%7D-%5Csum_%7Bf%20%5Cin%20Fuels%7Dfuel%5C_cost_f%5Ccdot%20x_%7Bf%2Cm%2Cb%7D-CO2%5C_price%5Ccdot%20exchange%5C_rate%5Ccdot0.8%5Ccdot%20energy_%7Bm%2Cb%7D-SO2%5C_reduced_%7Bm%2Cb%7D%5Ccdot%20SO2%5C_price%5CBigg%5D-FGD%5C_cost) |
| **Stockpile Inventory** | ![Stockpile](https://latex.codecogs.com/png.latex?%5Cbg_white%20%5Csum_%7Bm%2Cb%7D%20x_%7BStockpile%2C%20m%2C%20b%7D%20%5Cleq%20600%2C000) |
| **Biomass Limit** | ![Biomass](https://latex.codecogs.com/png.latex?%5Cbg_white%20energy_%7BBiomass%2C%20m%2C%20b%7D%20%5Cleq%20%5Ctext%7Bbiomass%5C_limit%7D%20%5Ctimes%20energy_%7Bm%2C%20b%7D%2C%20%5Cquad%20%5Cforall%20m%2Cb) |
| **Sulphur Bubble Limit** | ![SO2](https://latex.codecogs.com/png.latex?%5Cbg_white%20%5Csum_%7Bm%2Cb%7D%20SO2%5C_reduced_%7Bm%2Cb%7D%20%5Cleq%20SO2%5C_bubble%5C_limit) |
| **Capacity Limit** | ![Capacity](https://latex.codecogs.com/png.latex?%5Cbg_white%20energy_%7Bm%2C%20b%7D%20%5Cleq%20Cap%5C_MW%20%5Ctimes%20Hours_%7Bm%2Cb%7D%2C%20%5Cquad%20%5Cforall%20m%2Cb) |
| **No Coal (Summer Months)** | ![NoCoal](https://latex.codecogs.com/png.latex?%5Cbg_white%20x_%7Bf%2C%20m%2C%20b%7D%20%3D%200%2C%20%5Cquad%20%5Cforall%20f%20%5Cin%20mixes_3%2C%20m%20%5Cin%20%5C%7BJune%2C%20July%2C%20August%5C%7D%2C%20b%20%5Cin%20Bands)
---

## Tech Stack

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
Supervisors and teammates: Flora, Karan, Minh.
Optimization solver powered by Gurobi Optimizer.

LinkedIn → [Chandler Liu]([url](https://www.linkedin.com/in/chia-te-liu/))

Developed by Chia-Te Liu (Chandler) as part of the Alliance Manchester Business School course project on Operational Research & Optimization.
Supervisors and teammates: Flora, Karan, Minh.
Optimization solver powered by Gurobi Optimizer.

LinkedIn → linkedin.com/in/chia-te-liu
