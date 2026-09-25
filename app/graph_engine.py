import networkx as nx
from app.models import db, User, ResourceAccess, LoginEvent, GraphMetrics

def build_identity_access_graph():
    """
    Constructs a NetworkX graph representing:
    - User -> Role
    - Role -> Permission -> Resource
    - User -> Device
    - User -> Resource (Direct Activity)
    """
    G = nx.Graph()
    
    users = User.query.all()
    for u in users:
        u_node = f"USER:{u.user_id}"
        G.add_node(u_node, type='User', user_id=u.user_id, department=u.department or 'General')
        
        if u.role:
            role_node = f"ROLE:{u.role}"
            G.add_node(role_node, type='Role')
            G.add_edge(u_node, role_node, relation='HAS_ROLE')
            
        if u.department:
            dept_node = f"DEPT:{u.department}"
            G.add_node(dept_node, type='Department')
            G.add_edge(u_node, dept_node, relation='BELONGS_TO')
            
    # Add Login Device Edges
    logins = LoginEvent.query.all()
    for log in logins:
        u_node = f"USER:{log.user_id}"
        dev_node = f"DEV:{log.computer}"
        if G.has_node(u_node):
            G.add_node(dev_node, type='Device')
            G.add_edge(u_node, dev_node, relation='USED_DEVICE')
            
    # Add Resource Access Edges
    accesses = ResourceAccess.query.all()
    for acc in accesses:
        u_node = f"USER:{acc.user_id}"
        res_node = f"RES:{acc.resource_name}"
        if G.has_node(u_node):
            G.add_node(res_node, type='Resource', sensitive=acc.is_sensitive)
            G.add_edge(u_node, res_node, relation='ACCESSED', sensitive=acc.is_sensitive)
            
    return G

def compute_and_store_graph_metrics():
    """
    Computes Degree Centrality, Betweenness Centrality, Reachability,
    and Shortest Path to Sensitive Resources.
    """
    G = build_identity_access_graph()
    
    if len(G) == 0:
        return
        
    deg_centrality = nx.degree_centrality(G)
    bet_centrality = nx.betweenness_centrality(G)
    
    # Find all sensitive resources
    sensitive_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'Resource' and d.get('sensitive')]
    
    users = User.query.all()
    for u in users:
        u_node = f"USER:{u.user_id}"
        if not G.has_node(u_node):
            continue
            
        d_val = deg_centrality.get(u_node, 0.0)
        b_val = bet_centrality.get(u_node, 0.0)
        
        # Calculate Reachability (Number of reachable resources)
        reachable_resources = 0
        shortest_path_len = -1
        
        for s_node in sensitive_nodes:
            if nx.has_path(G, u_node, s_node):
                p_len = nx.shortest_path_length(G, u_node, s_node)
                if shortest_path_len == -1 or p_len < shortest_path_len:
                    shortest_path_len = p_len
                    
        for target in G.nodes():
            if G.nodes[target].get('type') == 'Resource' and nx.has_path(G, u_node, target):
                reachable_resources += 1
                
        # Calculate normalized graph risk score component (0-100) calibrated with Table 4.3 and Appendix C.2
        path_bonus = 20.0 if shortest_path_len == 1 else (10.0 if shortest_path_len == 2 else 0.0)
        reach_bonus = min(15.0, reachable_resources * 1.2)
        base_calc = (d_val * 220.0) + (b_val * 310.0) + path_bonus + reach_bonus
        if shortest_path_len == 1:
            base_calc += 10.0
        graph_risk = min(100.0, max(0.0, base_calc))
        
        # Store or update GraphMetrics
        gm = GraphMetrics.query.filter_by(user_id=u.user_id).first()
        if not gm:
            gm = GraphMetrics(user_id=u.user_id)
            db.session.add(gm)
            
        gm.degree_centrality = round(d_val, 4)
        gm.betweenness_centrality = round(b_val, 4)
        gm.resource_reachability = reachable_resources
        gm.shortest_sensitive_path = shortest_path_len
        gm.graph_risk_component = round(graph_risk, 2)
        
    db.session.commit()
