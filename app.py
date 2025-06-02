from flask import Flask, request, render_template
import xml.etree.ElementTree as ET
import json

app = Flask(__name__)

def parse_xml(xml_content):
    root = ET.fromstring(xml_content)
    repositories = []

    for project in root.findall('project'):
        repo_info = {
            "repository": project.get('name'),
            "target_path": project.get('path'),
            "remote": project.get('remote'),  # Capture the remote
            "branch": project.get('revision', '')  # Use revision as branch
        }
        repositories.append(repo_info)
    
    return repositories

def convert_to_dependencies(repositories, branch_mapping, remote_mapping):
    dependencies = []
    for repo in repositories:
        dep = {
            "remote": remote_mapping.get(repo["repository"], repo["remote"]),  # Use the provided remote or default
            "repository": repo["repository"],
            "target_path": repo["target_path"],
            "branch": branch_mapping.get(repo["repository"], repo["branch"] or '')  # Use user branch or default revision
        }
        dependencies.append(dep)
    
    return json.dumps(dependencies, indent=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    device_codename = ""
    xml_content = ""
    error_message = ""

    if request.method == 'POST':
        if 'xml_content' in request.form:
            # Process XML
            xml_content = request.form.get('xml_content')  # Capture the XML content entered
            device_codename = request.form.get('device_codename', "")
            if xml_content:
                repositories = parse_xml(xml_content)  # Parse XML content
                repositories_json = json.dumps(repositories)  # Serialize repositories
                return render_template('index.html', repositories=repositories, repositories_json=repositories_json, device_codename=device_codename, xml_content=xml_content, error_message=error_message)  # Pass back xml_content

        elif 'convert' in request.form:
            branch_mapping = {}
            remote_mapping = {}
            device_codename = request.form.get('device_codename', "")
            xml_content = request.form.get('xml_content', "")

            try:
                repositories_json = request.form.get('repositories')
                if not repositories_json:
                    raise json.JSONDecodeError("No repositories JSON", "", 0)
                repositories = json.loads(repositories_json)
            except json.JSONDecodeError as e:
                return render_template(
                    'index.html',
                    output="Error decoding JSON: " + str(e),
                    device_codename=device_codename,
                    xml_content=xml_content,
                    repositories_json="[]"
                )

            # Collect user-defined branches and remotes
            for repo in request.form:
                if repo.startswith('branch_'):
                    repo_name = repo.split('_', 1)[1]
                    branch_value = request.form[repo].strip()
                    branch_mapping[repo_name] = branch_value

                elif repo.startswith('remote_'):
                    repo_name = repo.split('_', 1)[1]
                    remote_mapping[repo_name] = request.form[repo].strip()

            remote_for_all = request.form.get('remoteForAll', '').strip()
            branch_for_all = request.form.get('branchForAll', '').strip()

            # Apply to all if provided
            if remote_for_all:
                for repo in repositories:
                    remote_mapping[repo["repository"]] = remote_for_all

            if branch_for_all:
                for repo in repositories:
                    branch_mapping[repo["repository"]] = branch_for_all

            # --- Check for empty fields ---
            missing_fields = False
            for repo in repositories:
                repo_name = repo["repository"]
                remote_val = remote_mapping.get(repo_name, "").strip()
                branch_val = branch_mapping.get(repo_name, "").strip()
                if not remote_val or not branch_val:
                    missing_fields = True
                    break

            if missing_fields:
                error_message = "All Remote and Branch fields must be filled out."
                return render_template(
                    'index.html',
                    repositories=repositories,
                    repositories_json=json.dumps(repositories),
                    device_codename=device_codename,
                    xml_content=xml_content,
                    error_message=error_message
                )
            # --- End check ---

            # Generate dependencies based on user branches and remotes
            dependencies = convert_to_dependencies(repositories, branch_mapping, remote_mapping)
            return render_template(
                'index.html',
                output=dependencies,
                repositories=repositories,
                repositories_json=json.dumps(repositories),
                device_codename=device_codename,
                branches=branch_mapping,
                xml_content=xml_content,
                error_message=""
            )

    return render_template('index.html', output='', repositories=[], device_codename='', xml_content='', error_message='')

if __name__ == '__main__':
    app.run(debug=False, port=5001)