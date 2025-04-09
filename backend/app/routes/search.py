import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.dependencies import db_dependency
from app.models.goals import Goal
from app.schemas.goals import GoalRead

router = APIRouter(prefix="/search", tags=["search"])


@router.websocket("/ws/search")
async def websocket_search(websocket: WebSocket, db: db_dependency):
    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_text()
            if message.strip():
                # Parse the message for query, page, and page size
                data = json.loads(message)
                query = data.get("query", "")
                page = data.get("page", 1)
                page_size = data.get("page_size", 3)

                # Fetch goals based on the search query with pagination
                goals = (
                    db.query(Goal)
                    .filter(
                        Goal.name.ilike(f"%{query}%")
                        | Goal.description.ilike(f"%{query}%")
                    )
                    .offset((page - 1) * page_size)  # Skip the previous pages
                    .limit(page_size)  # Limit the number of results
                    .all()
                )

                # Convert Goal objects to dictionaries for better readability
                result = []
                for goal in goals:
                    goal_dict = GoalRead.from_orm(goal).dict()
                    # Convert any datetime fields to ISO format strings
                    for key, value in goal_dict.items():
                        if hasattr(value, "isoformat"):
                            goal_dict[key] = value.isoformat()
                    result.append(goal_dict)

                await websocket.send_json(result)
            else:
                await websocket.send_json([])
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        print("Connection closed")


@router.get("/live-search", response_class=HTMLResponse)
async def live_search_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Search</title>
        <script>
    let socket = new WebSocket("ws://localhost:8000/search/ws/search");
    let currentPage = 1;
    const pageSize = 10; // Number of results per page

    socket.onopen = function() {
        console.log("WebSocket connection established");
    };

    socket.onmessage = function(event) {
        const result = JSON.parse(event.data);
        console.log("Search results:", result);
        // Handle the search results (e.g., display them on the page)
        const resultContainer = document.getElementById("results");
        resultContainer.innerHTML = ""; // Clear previous results
        if (result.length === 0) {
            resultContainer.innerHTML = "<div>No goals found.</div>";
        } else {
            result.forEach(goal => {
                const div = document.createElement("div");
                div.classList.add("goal-item");
                div.innerHTML = `
                    <h3>${goal.name}</h3>
                    <p>${goal.description || "No description available."}</p>
                `;
                resultContainer.appendChild(div);
            });
        }
    };

    function searchGoals() {
        const query = document.getElementById("searchInput").value;
        const data = {
            query: query,
            page: currentPage,
            page_size: pageSize
        };
        socket.send(JSON.stringify(data));
    }
</script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            .goal-item {
                border: 1px solid #ccc;
                padding: 10px 20px ;
                margin: 50px 10px;
                border-radius: 15px;
            }
            h3 {
                margin: 10;
                color: #333;
            }
            p {
                margin: 5px 0 0;
                color: #666;
            }
        </style>
    </head>
    <body>
        <h1>Live Goal Search</h1>
        <input type="text" id="searchInput" oninput="searchGoals()" placeholder="Search for goals...">
        <div id="results"></div>
    </body>
    </html>
    """
