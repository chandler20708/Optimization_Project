# International Coal Case Study – Optimization Web App

This project is an interactive web application built as part of the Mathematical Programming and Optimization coursework. It models and visualizes an energy generation planning problem for an international coal company, combining profit optimization with environmental constraints such as SO₂ and CO₂ emissions.

## 🎯 Objective

The optimization model determines the optimal fuel mix (coal, biomass, stockpile, etc.) across multiple months and demand bands to:
	•	Maximize total profit (revenue – fuel cost – carbon cost – investment)
	•	Respect generation capacity, SO₂ bubble limit, and biomass share constraints
	•	Evaluate trade-offs under different price and policy scenarios

⸻

## 🧩 Key Features

 • Gurobi-based LP/MILP model
Includes decision variables for fuel mix, emission levels, and FGD investment.
	•	Scenario and sensitivity analysis
Test how changes in electricity price, fuel cost, or emission price affect profit and fuel decisions.
	•	Streamlit web app interface
Allows users to adjust parameters, run optimization, and visualize results interactively.
	•	Dynamic visualizations
	•	Fuel mix bar chart (by month/band)
	•	Profit comparison across scenarios
	•	Constraint binding heatmaps
	•	Biomass share and emission composition plots
	•	Experiment logging
Stores model inputs and outputs in session state for later analysis.

## 🧰 Tech Stack
 •	Python 3.11+
	•	Gurobi 11.0
	•	Polars / Pandas
	•	Plotly
	•	Streamlit
	•	NumPy / SciPy

⸻

## 🚀 How to Run Locally

# Clone repository
git clone https://github.com/chandler20708/Optimization_Project.git
cd Optimization_Project/international_coal

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

## 📂 Project Structure
```international_coal/
│
├── app.py                  # Streamlit web interface
├── model.py                # Gurobi model setup and optimization logic
├── utils/                  # Helper functions (data loading, plotting, etc.)
├── data/                   # Input datasets (fuel cost, demand, emission factors)
├── results/                # Stored outputs and sensitivity reports
└── requirements.txt
```

## 📊 Example Use Cases
 •	Compare profit vs. emissions trade-offs under different CO₂ price policies
	•	Evaluate FGD investment viability with varying SO₂ bubbles
	•	Identify binding constraints via shadow price heatmaps
	•	Visualize biomass share evolution over months and periods

⸻

## 📖 Acknowledgments

Developed by Chia-Te Liu (Chandler) as part of the Alliance Manchester Business School course project on Operational Research & Optimization.
Supervisors and teammates: Flora, Karan, Minh.
Optimization solver powered by Gurobi Optimizer.

LinkedIn → linkedin.com/in/chia-te-liu
