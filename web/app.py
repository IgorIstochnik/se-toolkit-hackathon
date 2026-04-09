"""
Matrix Cafe Menu Web App

Simple web interface for browsing the Matrix cafe menu.
Deploy on the university VM so anyone can access it from their browser.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)


def get_db():
    """Get a fresh database connection for this request."""
    from database.db import MenuDatabase
    from nanobot.bot import MatrixCafeBot
    db = MenuDatabase('menu.db')
    bot = MatrixCafeBot(db)
    return db, bot


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Matrix Cafe Menu</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a5276, #2e86c1);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 1.5rem; margin-bottom: 5px; }
        .header p { opacity: 0.85; font-size: 0.9rem; }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .date-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .date-btn {
            padding: 8px 16px;
            border: 2px solid #2e86c1;
            border-radius: 20px;
            background: white;
            color: #2e86c1;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .date-btn.active, .date-btn:hover {
            background: #2e86c1;
            color: white;
        }
        .section {
            background: white;
            border-radius: 12px;
            margin-bottom: 15px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .section-header {
            background: #eaf2f8;
            padding: 12px 16px;
            font-weight: 600;
            color: #1a5276;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .item {
            padding: 12px 16px;
            border-bottom: 1px solid #f0f2f5;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .item:last-child { border-bottom: none; }
        .item-name { font-weight: 500; }
        .item-meta { font-size: 0.8rem; color: #666; margin-top: 4px; }
        .item-meta span { background: #eaf2f8; padding: 2px 8px; border-radius: 10px; margin-right: 5px; }
        .item-price {
            font-weight: 700;
            color: #1a5276;
            font-size: 1.1rem;
            white-space: nowrap;
            margin-left: 10px;
        }
        .combo-section {
            background: linear-gradient(135deg, #eaf2f8, #d4e6f1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .combo-section h3 { color: #1a5276; margin-bottom: 15px; }
        .budget-input {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 15px;
        }
        .budget-input input {
            padding: 10px 15px;
            border: 2px solid #2e86c1;
            border-radius: 8px;
            font-size: 1rem;
            width: 100px;
        }
        .budget-input button {
            padding: 10px 20px;
            background: #2e86c1;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.2s;
        }
        .budget-input button:hover { background: #1a5276; }
        .combo-result {
            background: white;
            border-radius: 8px;
            padding: 15px;
            display: none;
        }
        .combo-result.show { display: block; }
        .combo-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f0f2f5;
        }
        .combo-total {
            font-weight: 700;
            color: #1a5276;
            text-align: right;
            padding-top: 10px;
            font-size: 1.1rem;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🍽️ Matrix Cafe Menu</h1>
        <p>Innopolis University • Choose your meal for today</p>
    </div>

    <div class="container">
        <div class="date-selector" id="dates"></div>

        <div class="combo-section">
            <h3>💡 Balanced Lunch Combo</h3>
            <div class="budget-input">
                <span>Budget:</span>
                <input type="number" id="budget" placeholder="300" value="300" min="50" max="1000">
                <span>₽</span>
                <button onclick="getCombo()">Find Combo</button>
            </div>
            <div class="combo-result" id="comboResult"></div>
        </div>

        <div id="menu"></div>
    </div>

    <div class="footer">
        Matrix Cafe • Universitetskaya 1 • Open 8:00-20:00
    </div>

    <script>
        const dates = {{ dates | tojson }};
        let currentDate = dates[0];

        function renderDates() {
            const container = document.getElementById('dates');
            container.innerHTML = dates.map(d =>
                `<button class="date-btn ${d === currentDate ? 'active' : ''}" onclick="selectDate('${d}')">${d.slice(5)}</button>`
            ).join('');
        }

        function selectDate(date) {
            currentDate = date;
            renderDates();
            loadMenu();
        }

        async function loadMenu() {
            const res = await fetch(`/api/menu?date=${currentDate}`);
            const data = await res.json();
            const container = document.getElementById('menu');

            if (data.length === 0) {
                container.innerHTML = '<p style="text-align:center;padding:20px;">No menu available for this date.</p>';
                return;
            }

            const sections = {};
            data.forEach(item => {
                if (!sections[item.meal_type]) sections[item.meal_type] = [];
                sections[item.meal_type].push(item);
            });

            const order = ['salad', 'soup', 'main course', 'side dish', 'drink', 'bread'];
            const names = {
                'salad': '🥗 Salads',
                'soup': '🍲 Soups',
                'main course': '🍖 Main Course',
                'side dish': '🍚 Side Dishes',
                'drink': '🥤 Drinks',
                'bread': '🍞 Bread'
            };

            container.innerHTML = order
                .filter(s => sections[s])
                .map(type => `
                    <div class="section">
                        <div class="section-header">
                            <span>${names[type] || type}</span>
                            <span>${sections[type].length} items</span>
                        </div>
                        ${sections[type].map(item => `
                            <div class="item">
                                <div>
                                    <div class="item-name">${item.name}</div>
                                    <div class="item-meta">
                                        ${item.weight ? `<span>${item.weight}</span>` : ''}
                                        ${item.ingredients ? `<span>${item.ingredients.slice(0, 3).join(', ')}${item.ingredients.length > 3 ? '...' : ''}</span>` : ''}
                                    </div>
                                </div>
                                <div class="item-price">${item.price}₽</div>
                            </div>
                        `).join('')}
                    </div>
                `).join('');
        }

        async function getCombo() {
            const budget = document.getElementById('budget').value || 300;
            const res = await fetch(`/api/combo?budget=${budget}&date=${currentDate}`);
            const data = await res.json();

            const container = document.getElementById('comboResult');
            if (data.items && data.items.length > 0) {
                container.innerHTML = `
                    ${data.items.map(item => `
                        <div class="combo-item">
                            <span>${item.name} <small style="color:#666">(${item.meal_type})</small></span>
                            <strong>${item.price}₽</strong>
                        </div>
                    `).join('')}
                    <div class="combo-total">Total: ${data.total}₽</div>
                `;
                container.classList.add('show');
            } else {
                container.innerHTML = '<p>Could not create a combo within this budget. Try increasing it!</p>';
                container.classList.add('show');
            }
        }

        renderDates();
        loadMenu();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    db, _ = get_db()
    dates = sorted(db.conn.execute(
        "SELECT DISTINCT date FROM menu_items ORDER BY date DESC"
    ).fetchall(), key=lambda x: x[0], reverse=True)
    date_list = [row[0] for row in dates]
    db.close()
    return render_template_string(HTML_TEMPLATE, dates=date_list)


@app.route('/api/menu')
def get_menu():
    date = request.args.get('date', '')
    db, _ = get_db()
    if date:
        items = db.get_menu_by_date(date)
    else:
        items = db.get_latest_menu()
    db.close()
    return jsonify(items)


@app.route('/api/combo')
def get_combo():
    date = request.args.get('date', '')
    budget = float(request.args.get('budget', 300))
    db, _ = get_db()
    if date:
        menu_items = db.get_menu_by_date(date)
    else:
        menu_items = db.get_latest_menu()

    menu_by_type = {}
    for item in menu_items:
        mt = item.get('meal_type', 'other')
        if mt not in menu_by_type:
            menu_by_type[mt] = []
        menu_by_type[mt].append(item)

    combo = []
    combo_types = ['salad', 'soup', 'main course', 'drink']

    for mt in combo_types:
        if mt in menu_by_type:
            remaining = budget - sum(i.get('price', 0) for i in combo)
            affordable = [i for i in menu_by_type[mt] if i.get('price', 0) <= remaining]
            if affordable:
                affordable.sort(key=lambda x: x.get('price', 0))
                combo.append(affordable[0])

    total = sum(i.get('price', 0) for i in combo)
    db.close()
    return jsonify({
        'items': [{'name': i['name'], 'meal_type': i['meal_type'], 'price': i['price']} for i in combo],
        'total': total
    })


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    print(f"🍽️  Matrix Cafe Menu Helper - Web App")
    print(f"   Running on http://{args.host}:{args.port}")
    print(f"   Open in your browser to use it!")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
