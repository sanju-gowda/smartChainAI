
from flask import Flask, render_template_string
import pandas as pd
from sklearn.linear_model import LinearRegression
import math

app = Flask(__name__)

# Load inventory from the CSV file
def load_inventory():
    return pd.read_csv("inventory.csv")


# Analyze stock and recommend actions
def analyze_inventory(df):
    results = []

    for _, item in df.iterrows():
        stock = int(item["stock"])
        minimum = int(item["min_stock"])
        demand = int(item["daily_demand"])
        lead_time = int(item["lead_time_days"])

        days_left = stock / demand if demand > 0 else 0
        reorder_point = minimum + (demand * lead_time)

        if stock <= minimum:
            status = "CRITICAL"
            action = "Replenish stock immediately"
        elif stock <= reorder_point:
            status = "LOW"
            action = "Place a replenishment order"
        else:
            status = "NORMAL"
            action = "Continue monitoring"

        results.append({
            "product": item["product"],
            "stock": stock,
            "minimum": minimum,
            "days_left": round(days_left, 1),
            "status": status,
            "action": action
        })

    return results


HTML = """

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SmartChain AI | Dashboard</title>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #172033;
        }

        header {
            background: #103b46;
            color: white;
            padding: 24px 5%;
        }

        header h1 {
            margin: 0 0 8px;
            font-size: 30px;
        }

        header p {
            margin: 0;
            color: #d1e5e8;
        }

        nav {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            padding: 14px 5%;
            background: white;
            border-bottom: 1px solid #e2e8f0;
        }

        nav a {
            text-decoration: none;
            color: #0f766e;
            font-weight: bold;
            padding: 9px 12px;
            border-radius: 7px;
        }

        nav a:hover { background: #e6f5f2; }

        main {
            max-width: 1400px;
            margin: auto;
            padding: 28px 5%;
        }

        .intro {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 22px;
        }

        .intro h2 { margin: 0 0 6px; }
        .muted { color: #64748b; }

        .cards {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }

        .card, .panel {
            background: white;
            border: 1px solid #e7edf3;
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 5px 18px #17203308;
        }

        .card .label { color: #64748b; font-size: 14px; }
        .card .number { font-size: 34px; font-weight: bold; margin-top: 10px; }
        .card .note { font-size: 13px; margin-top: 8px; color: #64748b; }

        .teal { border-top: 4px solid #0f766e; }
        .amber { border-top: 4px solid #d97706; }
        .red { border-top: 4px solid #dc2626; }

        .charts {
            display: grid;
            grid-template-columns:  minmax(0, 3fr) minmax(0, 2fr);
            gap: 18px;
            margin-bottom: 24px;
        }

        .panel h3 { margin-top: 0; }
        .chart-box { height: 300px; position: relative; }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 700px;
        }

        th, td {
            text-align: left;
            padding: 15px 12px;
            border-bottom: 1px solid #e8edf3;
        }

        th {
            color: #64748b;
            font-size: 13px;
            text-transform: uppercase;
        }

        .status {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .CRITICAL { background: #fee2e2; color: #b91c1c; }
        .LOW { background: #fef3c7; color: #92400e; }
        .NORMAL { background: #dcfce7; color: #166534; }

        .action-link {
            display: inline-block;
            padding: 12px 16px;
            border-radius: 8px;
            background: #0f766e;
            color: white;
            text-decoration: none;
            font-weight: bold;
        }

        footer {
            text-align: center;
            padding: 24px;
            color: #64748b;
            font-size: 13px;
        }

        @media (max-width: 800px) {
            .cards { grid-template-columns: 1fr; }
            .charts { grid-template-columns: 1fr; }
            header h1 { font-size: 25px; }
        }
    </style>
</head>

<body>
<header>
    <h1>SmartChain AI</h1>
    <p>Intelligent Supply Chain Resilience Platform</p>
</header>


<nav>
    <a href="/">Overview</a>
    <a href="/forecast">AI Demand Forecast</a>
    <a href="/disruption">Disruption Simulator</a>
</nav>


<main>
    <section class="intro">
        <div>
            <h2>Supply Chain Overview</h2>
            <p class="muted">Monitor inventory health and identify potential shortages.</p>
        </div>
        <a class="action-link" href="/disruption">Run a disruption test</a>
    </section>

    <section class="cards">
        <div class="card teal">
            <div class="label">Total Products</div>
            <div class="number">{{ total }}</div>
            <div class="note">Products being monitored</div>
        </div>

        <div class="card amber">
            <div class="label">Low Stock</div>
            <div class="number">{{ low }}</div>
            <div class="note">Products approaching reorder levels</div>
        </div>

        <div class="card red">
            <div class="label">Critical Stock</div>
            <div class="number">{{ critical }}</div>
            <div class="note">Products at or below minimum stock</div>
        </div>
    </section>

    <section class="charts">
        <div class="panel">
            <h3>Stock vs Minimum Level</h3>
            <p class="muted">Compare available inventory with minimum stock requirements.</p>
            <div class="chart-box">
                <canvas id="stockChart"></canvas>
            </div>
        </div>

        <div class="panel">
            <h3>Inventory Risk Distribution</h3>
            <p class="muted">How many products fall into each risk category?</p>
            <div class="chart-box">
                <canvas id="riskChart"></canvas>
            </div>
        </div>
    </section>

    <section class="panel">
        <h3>Inventory Risk Analysis</h3>
        <p class="muted">Recommended actions are based on current stock and supplier lead time.</p>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Available Stock</th>
                        <th>Days Left</th>
                        <th>Status</th>
                        <th>Recommended Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td><strong>{{ item.product }}</strong></td>
                        <td>{{ item.stock }}</td>
                        <td>{{ item.days_left }}</td>
                        <td>
                            <span class="status {{ item.status }}">
                                {{ item.status }}
                            </span>
                        </td>
                        <td>{{ item.action }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </section>
</main>

<footer>
    SmartChain AI · Hackathon Prototype · Sample inventory data
</footer>

<script>
    const products = {{ items | map(attribute='product') | list | tojson }};
    const stocks = {{ items | map(attribute='stock') | list | tojson }};
    const minimums = {{ items | map(attribute='minimum') | list | tojson }};

    const normalCount = {{ items | selectattr('status', 'equalto', 'NORMAL') | list | length }};
    const lowCount = {{ low }};
    const criticalCount = {{ critical }};

    if (typeof Chart !== "undefined") {
        new Chart(document.getElementById("stockChart"), {
            type: "bar",
            data: {
                labels: products,
                datasets: [
                    {
                        label: "Current stock",
                        data: stocks,
                        backgroundColor: "#0f766e",
                        borderRadius: 5
                    },
                    {
                        label: "Minimum stock",
                        data: minimums,
                        backgroundColor: "#f59e0b",
                        borderRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        new Chart(document.getElementById("riskChart"), {
            type: "doughnut",
            data: {
                labels: ["Normal", "Low", "Critical"],
                datasets: [{
                    data: [normalCount, lowCount, criticalCount],
                    backgroundColor: ["#16a34a", "#f59e0b", "#dc2626"],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                }
            }
        });
    }
</script>
</body>
</html>

"""


@app.route("/")
def dashboard():
    df = load_inventory()
    items = analyze_inventory(df)

    return render_template_string(
        HTML,
        items=items,
        total=len(items),
        low=sum(i["status"] == "LOW" for i in items),
        critical=sum(i["status"] == "CRITICAL" for i in items)
    )


from flask import request

@app.route("/disruption", methods=["GET", "POST"])
def disruption():
    suppliers = pd.read_csv("suppliers.csv")
    products = load_inventory()

    selected_product = "Cooking Oil"
    unavailable_supplier = "Supplier A"
    recommendations = []
    shortage = None
    demand = 0
    stock = 0

    if request.method == "POST":
        selected_product = request.form["product"]
        unavailable_supplier = request.form["supplier"]

        product_rows = products[
            products["product"] == selected_product
        ]

        if not product_rows.empty:
            item = product_rows.iloc[0]
            stock = int(item["stock"])
            demand = int(item["daily_demand"])

            disruption_days = 7
            shortage = max(0, demand * disruption_days - stock)

            
            # Find alternative suppliers for the selected product
            alternatives = suppliers[
                (suppliers["product"] == selected_product)
                & (suppliers["supplier"] != unavailable_supplier)
            ].copy()

            # Ensure supplier data is numeric
            for col in [
                "available_stock", "lead_time_days", "cost_per_unit"
            ]:
                alternatives[col] = pd.to_numeric(
                    alternatives[col], errors="coerce"
                ).fillna(0)

            # Ignore suppliers with no stock or invalid delivery/cost data
            alternatives = alternatives[
                (alternatives["available_stock"] > 0)
                & (alternatives["lead_time_days"] > 0)
                & (alternatives["cost_per_unit"] > 0)
            ].copy()

            if not alternatives.empty:
                # Normalize delivery time and cost into scores from 0 to 1.
                # Higher scores mean faster delivery or lower cost.
                min_lead = alternatives["lead_time_days"].min()
                max_lead = alternatives["lead_time_days"].max()
                min_cost = alternatives["cost_per_unit"].min()
                max_cost = alternatives["cost_per_unit"].max()

                if max_lead > min_lead:
                    alternatives["speed_score"] = (
                        max_lead - alternatives["lead_time_days"]
                    ) / (max_lead - min_lead)
                else:
                    alternatives["speed_score"] = 1.0

                if max_cost > min_cost:
                    alternatives["cost_score"] = (
                        max_cost - alternatives["cost_per_unit"]
                    ) / (max_cost - min_cost)
                else:
                    alternatives["cost_score"] = 1.0

                # Stock score: full credit if the supplier can cover
                # the estimated shortage.
                if shortage > 0:
                    alternatives["stock_score"] = (
                        alternatives["available_stock"] / shortage
                    ).clip(upper=1.0)
                else:
                    alternatives["stock_score"] = 1.0

                # Weights: speed 50%, cost 30%, stock coverage 20%.
                alternatives["score"] = (
                    0.50 * alternatives["speed_score"]
                    + 0.30 * alternatives["cost_score"]
                    + 0.20 * alternatives["stock_score"]
                ) * 100

                # Put suppliers that can cover the full shortage first,
                # then rank by their weighted score.
                alternatives["sufficient"] = (
                    alternatives["available_stock"] >= shortage
                )

                alternatives = alternatives.sort_values(
                    ["sufficient", "score"],
                    ascending=[False, False]
                )

                for _, supplier in alternatives.iterrows():
                    sufficient = bool(supplier["sufficient"])

                    if sufficient:
                        reason = (
                            "Can cover shortage; ranked by speed, "
                            "cost and stock"
                        )
                    else:
                        reason = (
                            "Partial stock only; additional supply needed"
                        )

                    recommendations.append({
                        "name": supplier["supplier"],
                        "stock": int(supplier["available_stock"]),
                        "lead_time": int(supplier["lead_time_days"]),
                        "cost": float(supplier["cost_per_unit"]),
                        "sufficient": sufficient,
                        "score": round(float(supplier["score"]), 1),
                        "reason": reason
                    })
                    
    # Generate an explainable action plan
    action_plan = []

    if shortage is None:
     shortage = 0 
    if shortage > 0:
        action_plan.append(
            f"Address the shortage of {shortage:.0f} units as soon as possible."
        )

        suitable_suppliers = [
            supplier for supplier in recommendations
            if supplier["sufficient"]
        ]

        if suitable_suppliers:
            best_supplier = suitable_suppliers[0]

            action_plan.append(
                f"Prioritize {best_supplier['name']}: "
                f"it can cover the shortage with a lead time of "
                f"{best_supplier['lead_time']} days."
            )

            backup_suppliers = [
                supplier for supplier in suitable_suppliers
                if supplier["name"] != best_supplier["name"]
            ]

            if backup_suppliers:
                action_plan.append(
                    f"Keep {backup_suppliers[0]['name']} as a backup supplier."
                )
        else:
            action_plan.append(
                "No single alternative supplier can cover the full shortage. "
                "Consider splitting the order across suppliers."
            )
    else:
        action_plan.append(
            "No immediate shortage is projected for the selected scenario."
        )

    action_plan.append(
        "Monitor inventory daily until replacement stock arrives."
    )
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>SmartChain AI - Disruption Simulator</title>
      <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Inter, "Segoe UI", Arial, sans-serif; background: #f3f6fb; color: #172033; line-height: 1.55; padding: 0 0 32px; }
        body::before { content: ""; display: block; height: 7px; background: linear-gradient(90deg, #0f766e, #2dd4bf, #93c5fd); }
        .panel { background: #fff; padding: clamp(20px, 4vw, 34px); border: 1px solid #e3eaf2; border-radius: 20px; max-width: 1120px; margin: 28px auto; box-shadow: 0 14px 40px rgba(20, 40, 70, .07); }
        h1 { color: #103b46; font-size: clamp(27px, 4vw, 36px); letter-spacing: -.7px; margin: 0 0 8px; }
        h2 { color: #163e4a; margin-top: 30px; }
        p { color: #64748b; }
        label { display: block; font-weight: 700; margin: 12px 0 5px; color: #334155; }
        select, button { display: block; padding: 12px 14px; margin: 6px 0 16px; width: 100%; border: 1px solid #d6e0eb; border-radius: 10px; background: #fff; color: #172033; font: inherit; }
        select:focus { outline: 3px solid #99f6e4; border-color: #0f766e; }
        button { background: #0f766e; color: white; border: 0; font-weight: 700; cursor: pointer; box-shadow: 0 5px 12px rgba(15, 118, 110, .18); transition: transform .15s ease, background .15s ease; }
        button:hover { background: #115e59; transform: translateY(-1px); }
        table { width: 100%; border-collapse: collapse; min-width: 720px; }
        th, td { padding: 14px 12px; border-bottom: 1px solid #e8eef5; text-align: left; vertical-align: top; }
        th { background: #f8fafc; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
        tr:hover td { background: #fbfdff; }
        .action-plan { margin-top: 24px; padding: 20px 24px; border: 1px solid #b7e4dc; border-left: 5px solid #0f766e; border-radius: 14px; background: linear-gradient(135deg, #f0fdfa, #f8fffe); }
        .action-plan h2 { margin-top: 0; color: #0f5e59; }
        .action-plan li { padding: 5px 0 5px 4px; }
        .good { color: #15803d; font-weight: bold; }
        .warn { color: #b45309; font-weight: bold; }
        a { color: #0f766e; font-weight: 700; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .panel > p:last-child { border-top: 1px solid #e8eef5; padding-top: 18px; margin-top: 28px; }
        @media (max-width: 760px) { .panel { margin: 16px 12px; padding: 20px 16px; } table { font-size: 13px; } th, td { padding: 10px 8px; } }
      </style>
    </head>
    <body>
      <div class="panel">
        <h1>Supply Chain Disruption Simulator</h1>
        <p>Simulate a supplier failure and find alternatives.</p>

        <form method="POST">
          <label>Product</label>
          <select name="product">
            {% for p in products %}
            <option value="{{ p }}"
              {% if p == selected_product %}selected{% endif %}>
              {{ p }}
            </option>
            {% endfor %}
          </select>

          <label>Unavailable supplier</label>
          <select name="supplier">
            {% for s in suppliers %}
            <option value="{{ s }}"
              {% if s == unavailable_supplier %}selected{% endif %}>
              {{ s }}
            </option>
            {% endfor %}
          </select>

          <button type="submit">Simulate disruption</button>
        </form>

        {% if shortage is not none %}
          <h2>Impact assessment</h2>
          <p>Current stock: {{ stock }}</p>
          <p>Daily demand: {{ demand }}</p>
          <p>Estimated 7-day shortage:
             <strong>{{ shortage }} units</strong></p>

          <h2>Alternative suppliers</h2>
          {% if recommendations %}
         
<table>
    <tr>
        <th>Rank</th>
        <th>Supplier</th>
        <th>Available</th>
        <th>Lead time</th>
        <th>Cost/unit</th>
        <th>Score</th>
        <th>Assessment</th>
    </tr>
    {% for r in recommendations %}
    <tr>
        <td>{{ loop.index }}</td>
        <td>
            <strong>{{ r.name }}</strong>
            {% if loop.first and r.sufficient %}
            <br><small>Top recommendation</small>
            {% endif %}
        </td>
        <td>{{ r.stock }}</td>
        <td>{{ r.lead_time }} days</td>
        <td>{{ "%.2f"|format(r.cost) }}</td>
        <td>{{ r.score }}/100</td>
        <td>
            {{ "Sufficient stock" if r.sufficient
               else "Insufficient stock" }}
            <br>
            <small>{{ r.reason }}</small>
        </td>
    </tr>
    {% endfor %}
</table>

<div class="action-plan">
    <h2>Smart AI Action Plan</h2>
    <p>Recommended actions based on the current disruption:</p>
    <ol>
        {% for action in action_plan %}
            <li>{{ action }}</li>
        {% endfor %}
    </ol>
</div>

          {% else %}
          <p>No alternative suppliers have available stock.</p>
          {% endif %}
        {% endif %}

        <p>
    <a href="/">Overview</a> |
    <a href="/forecast">AI Demand Forecast</a> |
    <a href="/disruption">Disruption Simulator</a>
</p>
      </div>
    </body>
    </html>
    """,
    products=products["product"].tolist(),
    suppliers=sorted(suppliers["supplier"].unique().tolist()),
    selected_product=selected_product,
    unavailable_supplier=unavailable_supplier,
    recommendations=recommendations,
    shortage=shortage,
    stock=stock,
    demand=demand
    )


@app.route("/forecast")
def forecast():
    sales = pd.read_csv("sales_history.csv")
    inventory = load_inventory()

    forecasts = []

    for _, item in inventory.iterrows():
        history = sales[sales["product"] == item["product"]]

        if len(history) < 2:
            continue

        X = history[["day"]]
        y = history["units_sold"]

        model = LinearRegression()
        model.fit(X, y)

        # Predict demand for the next 7 days
        future_days = pd.DataFrame({
            "day": range(int(history["day"].max()) + 1,
                         int(history["day"].max()) + 8)
        })

        predictions = model.predict(future_days[["day"]])
        predictions = [max(0, math.ceil(p)) for p in predictions]

        predicted_demand = sum(predictions)
        stock = int(item["stock"])
        lead_time = int(item["lead_time_days"])
        daily_forecast = sum(predictions) / 7

        reorder_target = math.ceil(daily_forecast * (lead_time + 7))
        shortage = max(0, predicted_demand - stock)

        if stock < predicted_demand:
            status = "SHORTAGE RISK"
            action = f"Plan for at least {shortage} additional units"
        elif stock < reorder_target:
            status = "REORDER SOON"
            action = f"Consider replenishing toward {reorder_target} units"
        else:
            status = "SUFFICIENT"
            action = "Continue monitoring stock"

        forecasts.append({
            "product": item["product"],
            "stock": stock,
            "predicted": predicted_demand,
            "shortage": shortage,
            "status": status,
            "action": action
        })

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>SmartChain AI - Demand Forecast</title>
        <style>
            * { box-sizing: border-box; }
            body { margin: 0; padding: 0 0 32px; font-family: Inter, "Segoe UI", Arial, sans-serif; background: #f3f6fb; color: #172033; line-height: 1.55; }
            body::before { content: ""; display: block; height: 7px; background: linear-gradient(90deg, #0f766e, #2dd4bf, #93c5fd); }
            .panel { max-width: 1180px; margin: 28px auto; padding: clamp(20px, 4vw, 34px); background: #fff; border: 1px solid #e3eaf2; border-radius: 20px; box-shadow: 0 14px 40px rgba(20, 40, 70, .07); }
            h1 { color: #103b46; font-size: clamp(27px, 4vw, 36px); letter-spacing: -.7px; margin: 0 0 8px; }
            .muted { color: #64748b; }
            .table-wrap { overflow-x: auto; margin-top: 22px; border: 1px solid #e8eef5; border-radius: 12px; }
            table { width: 100%; border-collapse: collapse; min-width: 760px; }
            th, td { text-align: left; padding: 15px 12px; border-bottom: 1px solid #e8eef5; vertical-align: top; }
            th { color: #64748b; background: #f8fafc; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }
            tbody tr:hover td { background: #fbfdff; }
            .risk { color: #b91c1c; font-weight: bold; }
            .soon { color: #b45309; font-weight: bold; }
            .ok { color: #15803d; font-weight: bold; }
            a { color: #0f766e; font-weight: 700; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .panel > p:last-child { border-top: 1px solid #e8eef5; padding-top: 18px; margin-top: 28px; }
            @media (max-width: 760px) { .panel { margin: 16px 12px; padding: 20px 16px; } th, td { padding: 11px 9px; } }
        </style>
    </head>
    <body>
        <div class="panel">
            <h1>AI Demand Forecast</h1>
            <p class="muted">
                Estimated demand for the next seven days,
                based on sample historical sales.
            </p>

            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Current Stock</th>
                            <th>Forecast Demand</th>
                            <th>Estimated Shortage</th>
                            <th>Risk</th>
                            <th>Recommended Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for f in forecasts %}
                        <tr>
                            <td>{{ f.product }}</td>
                            <td>{{ f.stock }}</td>
                            <td>{{ f.predicted }} units</td>
                            <td>{{ f.shortage }} units</td>
                            <td class="{{ 'risk' if f.status == 'SHORTAGE RISK' else ('soon' if f.status == 'REORDER SOON' else 'ok') }}">
                                {{ f.status }}
                            </td>
                            <td>{{ f.action }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <p>
    <a href="/">Overview</a> |
    <a href="/forecast">AI Demand Forecast</a> |
    <a href="/disruption">Disruption Simulator</a>
</p>
        </div>
    </body>
    </html>
    """, forecasts=forecasts)

if __name__ == "__main__":
    app.run(debug=True)
