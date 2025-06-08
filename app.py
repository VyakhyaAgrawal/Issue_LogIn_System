from flask import Flask, render_template, redirect, url_for, session, request
import mysql.connector
from config import db_config

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Home page to choose user type
@app.route('/')
def home():
    return render_template('home.html')

# Redirect based on role selected
@app.route('/select_role', methods=['POST'])
def select_role():
    role = request.form.get('role')
    if role == 'public':
        return redirect(url_for('public_issue'))
    elif role == 'team':
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))

# Team login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        if user == 'team' and password == 'sify123':
            session['team_user'] = user
            return redirect(url_for('team_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# Team dashboard
@app.route('/dashboard')
def team_dashboard():
    if 'team_user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('team_user', None)
    return redirect(url_for('home'))

# Public issue submission
@app.route('/public_issue', methods=['GET', 'POST'])
def public_issue():
    if request.method == 'POST':
        name_of_exam = request.form['name_of_exam']
        venue_code = request.form['venue_code']
        issue_on = request.form['issue_on']
        issue_priority = request.form['issue_priority']
        issue_reported = request.form['issue_reported']
        issue_reported_by = request.form['issue_reported_by']
        issue_reported_to = request.form['issue_reported_to']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Check if venue exists
            cursor.execute("SELECT COUNT(*) FROM venues WHERE venue_code = %s", (venue_code,))
            venue_exists = cursor.fetchone()[0]

            if venue_exists == 0:
                return render_template("public_issue.html", message="❌ Invalid venue code.", submitted_issue=None)

            insert_query = """
                INSERT INTO issues (
                    NAME_OF_EXAM, ISSUE_ON, VENUE_CODE, ISSUE_PRIORITY,
                    ISSUE_REPORTED, ISSUE_REPORTED_BY, ISSUE_REPORTED_TO, STATUS
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                name_of_exam, issue_on, venue_code, issue_priority,
                issue_reported, issue_reported_by, issue_reported_to, 'Unsolved'
            )

            cursor.execute(insert_query, values)
            conn.commit()

            submitted_issue = {
                'name_of_exam': name_of_exam,
                'venue_code': venue_code,
                'issue_on': issue_on,
                'issue_priority': issue_priority,
                'issue_reported': issue_reported,
                'issue_reported_by': issue_reported_by,
                'issue_reported_to': issue_reported_to
            }

            return render_template("public_issue.html", message="✅ Issue submitted successfully!", submitted_issue=submitted_issue)

        except Exception as e:
            return render_template("public_issue.html", message=f"❌ Error: {str(e)}", submitted_issue=None)

        finally:
            cursor.close()
            conn.close()

    return render_template("public_issue.html", submitted_issue=None)

# View all issues (team user)
@app.route('/view_issues')
def view_issues():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM issues ORDER BY ISSUE_DATE DESC")
    issues = cursor.fetchall()
    conn.close()

    return render_template("view_issues.html", issues=issues)

@app.route('/filter_issues', methods=['GET', 'POST'])
def filter_issues():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    query = """
        SELECT issues.* FROM issues
        JOIN venues ON issues.VENUE_CODE = venues.VENUE_CODE
        WHERE 1=1
    """
    filters = []

    # Initialize for both GET and POST
    region = None
    priority = None

    if request.method == 'POST':
        region = request.form.get('region')
        priority = request.form.get('priority')

        if region and region != 'all':
            query += " AND venues.REGION = %s"
            filters.append(region.lower())  # assuming lowercase region values in DB

        if priority and priority != 'all':
            query += " AND issues.ISSUE_PRIORITY = %s"
            filters.append(priority)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, filters)
    issues = cursor.fetchall()
    conn.close()

    return render_template("filter_issues.html", issues=issues,
                           selected_region=region,
                           selected_priority=priority)


@app.route('/edit_choice', methods=['GET', 'POST'])
def edit_choice():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form['action']
        if action == 'edit_details':
            return redirect(url_for('edit_issue_form'))
        elif action == 'update_status':
            return redirect(url_for('update_status_form'))
    
    return render_template("edit_choice.html")
@app.route('/edit_issue_form', methods=['GET', 'POST'])
def edit_issue_form():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    message = None
    if request.method == 'POST':
        issue_id = request.form['issue_id']
        priority = request.form['issue_priority']
        reported_by = request.form['issue_reported_by']
        reported_to = request.form['issue_reported_to']

        updates = []
        values = []

        if priority:
            updates.append("ISSUE_PRIORITY = %s")
            values.append(priority)
        if reported_by:
            updates.append("ISSUE_REPORTED_BY = %s")
            values.append(reported_by)
        if reported_to:
            updates.append("ISSUE_REPORTED_TO = %s")
            values.append(reported_to)

        if updates:
            values.append(issue_id)
            query = f"UPDATE issues SET {', '.join(updates)} WHERE ISSUE_ID = %s"

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            conn.close()

            message = "✅ Issue updated successfully!"
        else:
            message = "⚠️ No fields selected to update."

    return render_template("edit_issue_form.html", message=message)
@app.route('/update_status_form', methods=['GET', 'POST'])
def update_status_form():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    message = None
    if request.method == 'POST':
        issue_id = request.form['issue_id']
        status = request.form['status']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE issues SET STATUS = %s WHERE ISSUE_ID = %s", (status, issue_id))
        conn.commit()
        conn.close()

        message = f"✅ Issue ID {issue_id} marked as {status}."

    return render_template("update_status_form.html", message=message)
@app.route('/delete_issue', methods=['GET', 'POST'])
def delete_issue():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    issues = []
    selected_region = None
    message = None

    if request.method == 'POST':
        selected_region = request.form['region']
        region_prefix = selected_region[0].upper() + '%'  # e.g., N%, S%

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM issues WHERE VENUE_CODE LIKE %s", (region_prefix,))
        issues = cursor.fetchall()
        conn.close()

    return render_template("delete_issue.html", issues=issues, selected_region=selected_region, message=message)
@app.route('/delete_issue_confirm', methods=['POST'])
def delete_issue_confirm():
    if 'team_user' not in session:
        return redirect(url_for('login'))

    issue_id = request.form['issue_id']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM issues WHERE ISSUE_ID = %s", (issue_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()

        if rows_deleted == 0:
            message = f"❌ No issue found with ID {issue_id}."
        else:
            message = f"✅ Issue ID {issue_id} deleted successfully!"

    except Exception as e:
        message = f"❌ Error: {str(e)}"

    return render_template("delete_issue.html", issues=[], selected_region=None, message=message)


if __name__ == '__main__':
    app.run(debug=True)
