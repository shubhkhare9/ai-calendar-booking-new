from langgraph.graph import StateGraph

# A simple state class (just a dictionary)
class MyState(dict):
    pass

# A single function node
def node(state):
    print("🧠 Node ran with state:", state)
    return state

# Define the LangGraph flow
g = StateGraph(MyState)
g.add_node("start", node)
g.set_entry_point("start")
g.set_finish_point("start")
g = g.compile()

# Run the flow with dummy input
output = g.invoke(MyState({"message": "Hello"}))
print("✅ Final output:", output)
