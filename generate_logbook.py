import datetime

start_date = datetime.date(2026, 2, 2)
end_date = datetime.date(2026, 5, 1)

current_date = start_date
valid_dates = []

while current_date <= end_date:
    if current_date.weekday() < 5: # Monday to Friday
        if datetime.date(2026, 3, 9) <= current_date <= datetime.date(2026, 3, 13):
            pass
        else:
            valid_dates.append(current_date)
    current_date += datetime.timedelta(days=1)

entries = [
    # Week 1: Feb 2 - Feb 6 (Project Kickoff & Requirements)
    ("Today was the official launch of the 'LogiFlow AI' project. The goal is to build a Smart PDF Logbook Editor and Generator to automate the tedious process of writing daily project logs.", "Attended the kickoff meeting. Finalized the project scope and the core tech stack (React, FastAPI, MongoDB, Gemini).", "Learned that the primary pain point for students is context continuity—remembering what was written the previous month.", "Microsoft Teams, Markdown", "Successfully defined the project scope and tech stack."),
    ("Focused on researching the AI orchestration requirements. A single LLM prompt won't work for generating a 30-day logbook due to context limits.", "Conducted a literature review on multi-agent systems and LangGraph for iterative generation.", "Observed that LangGraph allows for stateful, cyclical agent execution, which is perfect for our day-by-day generation approach.", "Google Scholar, LangGraph Docs", "Decided on LangGraph as the core AI orchestration framework."),
    ("Started drafting the Project Requirements Document (PRD). Defined the functional scope for both manual PDF editing and AI generation.", "Drafted the Problem Understanding and Functional Scope sections of the PRD. Outlined the key user flows.", "Learned that clearly separating the manual canvas editor from the AI generation pipeline will make development much smoother.", "Microsoft Word, Draw.io", "Drafted the initial version of the PRD."),
    ("Continuing PRD refinement, focusing on system architecture. We need a modern frontend to handle complex canvas interactions.", "Mapped out the pipeline: React Frontend -> FastAPI Backend -> LangGraph Pipeline -> PyMuPDF injection.", "Observed that handling PDFs in the browser (via pdf.js) and rendering them on a canvas (Konva) is the best approach for interactive editing.", "Draw.io, System Design", "Finalized the high-level system architecture."),
    ("Final day of the planning phase. Presented the PRD and architecture to the mentor.", "Reviewed PRD, incorporated mentor feedback, and set up the GitHub repository.", "Learned the importance of asynchronous backend processing, as LLM calls can take several seconds to complete.", "GitHub, VS Code", "Completed the first milestone: PRD Approval."),

    # Week 2: Feb 9 - Feb 13 (Frontend & Backend Setup)
    ("Starting the development phase! Bootstrapped the React frontend today.", "Initialized a React 19 project using Vite. Set up ESLint and Prettier for code consistency.", "Vite is incredibly fast compared to Create React App. The hot module replacement (HMR) is near-instant.", "React, Vite, Node.js", "Successfully bootstrapped the frontend application."),
    ("Focused on setting up the FastAPI backend environment today.", "Created a Python virtual environment, installed FastAPI and Uvicorn, and set up the basic project structure.", "FastAPI's native support for async/await makes it a perfect fit for our AI-heavy, I/O bound application.", "Python, FastAPI, Uvicorn", "Backend server is up and running locally."),
    ("Working on integrating MongoDB to store user context and generation states.", "Set up a local MongoDB instance. Installed the 'motor' asynchronous driver for Python and created the database connection logic.", "Using an async driver is crucial so database queries don't block the FastAPI event loop.", "MongoDB, Motor", "Successfully connected the backend to the database."),
    ("Today we defined the core API endpoints for the application.", "Created Pydantic models for user inputs (dates, project description) and defined the FastAPI router for the '/generate' endpoint.", "Pydantic makes data validation extremely easy and automatically generates Swagger documentation.", "FastAPI, Pydantic", "API routing and data validation schemas established."),
    ("Implemented Cross-Origin Resource Sharing (CORS) and tested the connection between the React frontend and FastAPI backend.", "Configured CORS middleware in FastAPI to accept requests from the Vite dev server. Wrote a simple Axios fetch on the frontend.", "CORS issues are a common headache, but setting them up early prevents integration problems later.", "Axios, CORS Middleware", "Successfully established frontend-backend communication."),

    # Week 3: Feb 16 - Feb 20 (PDF Rendering & Canvas UI)
    ("Starting work on the interactive PDF viewer. The goal is to render a PDF page as an image on a web canvas.", "Installed 'pdfjs-dist' and wrote a utility function to load a PDF document and extract the first page as an image data URL.", "Extracting PDF pages as images is necessary to layer an interactive drawing/text canvas on top of them.", "React, pdf.js", "Successfully rendered a PDF page within the React app."),
    ("Integrating Konva.js to create the interactive canvas layer over the PDF.", "Installed 'react-konva'. Set up a Stage and Layer component, placing the extracted PDF image as the background of the canvas.", "Konva provides a high-performance 2D canvas API with React bindings, making it easy to manage draggable elements.", "React-Konva", "Canvas layer successfully overlaid on the PDF rendering."),
    ("Working on adding draggable text elements to the Konva canvas.", "Created a custom Text component in Konva that supports drag-and-drop. Added state to track the X and Y coordinates of text elements.", "Managing canvas state in React requires careful synchronization to ensure smooth dragging.", "Konva.js, React State", "Implemented draggable text elements on the PDF canvas."),
    ("Adding interaction to the text elements: double-clicking to edit.", "Implemented an event listener for double-clicks on Konva text nodes, which temporarily replaces the canvas text with an HTML textarea.", "Seamlessly swapping between canvas text and a DOM textarea is the standard approach for rich canvas editing.", "HTML/CSS, DOM manipulation", "Enabled inline text editing on the canvas."),
    ("Refining the canvas UI. Adding controls for text size, color, and font family.", "Built a toolbar component that updates the properties of the currently selected Konva text node.", "Centralizing the state for the 'selected element' allows the toolbar to dynamically update the correct text node.", "React Context/State", "Canvas UI now supports basic text styling."),

    # Week 4: Feb 23 - Feb 27 (Rich Text Editing & PyMuPDF)
    ("Today we started integrating 'Tiptap' for a more robust rich-text experience outside the canvas.", "Installed Tiptap and its starter kit. Replaced standard textareas in our forms with the Tiptap editor.", "Tiptap is headless, giving us complete control over the styling and UX of the text editor.", "Tiptap, ProseMirror", "Successfully integrated a rich text editor for logbook inputs."),
    ("Customizing the Tiptap editor to support lists, bold, italic, and dynamic variable insertion.", "Added extensions for BulletList, OrderedList, and a custom extension to insert placeholders like '{{date}}'.", "Extending Tiptap is relatively straightforward thanks to its modular architecture.", "Tiptap Extensions", "Rich text editor now supports complex formatting."),
    ("Shifting focus back to the backend. We need to be able to manipulate actual PDF files server-side.", "Installed 'PyMuPDF' (pymupdf). Wrote a basic script to open a PDF, find a specific page, and print its metadata.", "PyMuPDF is significantly faster and more feature-rich than older libraries like PyPDF2.", "Python, PyMuPDF", "Verified server-side PDF reading capabilities."),
    ("Implementing server-side text injection using PyMuPDF.", "Developed a function that takes X/Y coordinates from the frontend canvas and uses 'page.insert_text()' to bake the text directly into the PDF.", "Coordinating the coordinate system between the frontend Konva canvas and the backend PyMuPDF page is challenging.", "PyMuPDF text insertion", "Successfully injected text into a PDF document."),
    ("Refining the coordinate mapping between Konva and PyMuPDF.", "Wrote a transformation matrix to convert browser pixels to PDF points (which are 72 DPI). Handled scaling and resolution differences.", "Understanding DPI and PDF coordinate systems is crucial for accurate text placement.", "Math, Transformations", "Achieved pixel-perfect alignment between frontend and backend PDFs."),

    # Week 5: Mar 2 - Mar 6 (AI Architecture & LangGraph)
    ("Starting the core AI integration. The first step is setting up LangChain and accessing the Gemini API.", "Installed 'langchain-google-genai'. Set up API keys and wrote a basic script to prompt the Gemini-1.5-Pro model.", "Gemini 1.5 Pro offers an enormous context window, which is great for analyzing project documents.", "LangChain, Google Gemini", "Successfully authenticated and communicated with the Gemini API."),
    ("Designing the multi-agent orchestration architecture using LangGraph.", "Sketched the state graph: Planner Node -> Writer Node -> Context Manager Node. Defined the shared 'State' dictionary.", "LangGraph's stateful approach allows agents to pass data to each other iteratively, preventing context loss.", "LangGraph, State Management", "Defined the multi-agent state schema and graph structure."),
    ("Implementing the 'Planner Agent'. This agent breaks down a 30-day period into logical daily tasks.", "Wrote the prompt and LangChain runnable for the Planner. It takes the project description and returns a structured JSON array of daily overviews.", "Using structured output (JSON parsing) is essential to ensure the Planner's output can be read by the Writer agent.", "Prompt Engineering", "Planner agent successfully generates a monthly breakdown."),
    ("Implementing the 'Writer Agent'. This agent takes a daily overview and expands it into a detailed logbook entry.", "Developed the Writer node. It generates 5 specific sections: Tasks, Learnings, Tools, Challenges, and Outcomes for a given day.", "Instructing the LLM to adhere to a strict markdown format ensures consistent logbook generation.", "LangGraph Nodes", "Writer agent generates detailed, formatted daily entries."),
    ("Testing the interaction between the Planner and the Writer.", "Built a LangGraph workflow that calls the Planner, iterates over the resulting array, and calls the Writer for each day.", "Running the Writer sequentially for 30 days is too slow. We will need to implement parallel execution next.", "LangGraph Workflows", "Successfully chained the Planner and Writer agents together."),

    # (Skipping Mar 9 - Mar 13 as requested)

    # Week 7: Mar 16 - Mar 20 (Parallel Execution & Fallbacks)
    ("Optimizing the generation pipeline. We are implementing parallel execution for the Writer agent to drastically reduce generation time.", "Refactored the LangGraph workflow to use 'Send' API for dynamic parallel node mapping across the days generated by the planner.", "Parallel execution reduced the 30-day generation time from 3 minutes to about 40 seconds.", "LangGraph Parallelism", "Significantly improved AI generation speed."),
    ("Today we addressed API rate limits. Generating many days in parallel often hits Gemini's rate limits.", "Implemented LangChain's built-in retry mechanisms and added a custom exponential backoff strategy.", "Handling API rate limits gracefully is critical for a production AI application.", "Exponential Backoff", "Pipeline is now resilient to temporary API throttling."),
    ("Implementing a robust fallback mechanism using Groq and Llama 3.", "Integrated 'langchain-groq'. Configured the graph to fall back to Llama 3 if Gemini fails or times out repeatedly.", "Groq's LPU inference engine is incredibly fast, making it an excellent fallback provider.", "Groq API, Fallbacks", "Established a multi-model fallback architecture for high availability."),
    ("Working on the 'Context Manager Agent'. This agent summarizes the generated month to maintain continuity.", "Developed a node that runs after all Writer nodes finish. It reads the full month's output and writes a concise summary to MongoDB.", "This summary acts as the 'memory' for the next generation cycle, solving the context continuity problem.", "Context Summarization", "Context Manager successfully stores monthly state in the database."),
    ("Testing the month-to-month continuity.", "Simulated generating logs for Month 1, then requested Month 2. Passed the stored summary into the Planner agent for Month 2.", "The Planner successfully referenced tasks completed in Month 1, ensuring a logical progression without repetition.", "Integration Testing", "Verified the long-term memory and continuity of the AI pipeline."),

    # Week 8: Mar 23 - Mar 27 (Formatting & PDF Construction)
    ("Now that the AI generates the content, we need to format it beautifully into the PDF template.", "Wrote a Python parser that takes the Markdown output from the Writer agent and converts it into specific text blocks (Title, Body, Bullets).", "Parsing markdown into distinct geometric elements is necessary for precise PDF rendering.", "Markdown Parsing", "Successfully parsed AI output into renderable blocks."),
    ("Implementing text wrapping and pagination for PyMuPDF.", "Developed an algorithm that calculates the width of text strings and automatically wraps them to fit within the designated bounding boxes on the PDF page.", "Text wrapping requires calculating the precise width of strings based on the chosen font and size.", "PyMuPDF Text Handling", "Implemented dynamic text wrapping for generated content."),
    ("Handling multi-page overflow in the PDF generation.", "Added logic to detect when text exceeds the vertical space of a logbook page and automatically duplicate the template page to continue the text.", "Managing PDF page duplication and linking is complex but necessary for variable-length AI content.", "PDF Pagination", "System now automatically handles overflowing logbook entries."),
    ("Today we focused on styling the injected text.", "Configured PyMuPDF to use custom TrueType fonts (TTF) that match the user's selected style. Applied bolding to headers and bullet points.", "Embedding custom fonts in PDFs ensures the document looks the same on any device.", "Font Embedding", "Enhanced the visual quality of the generated PDFs."),
    ("Refining the date mapping logic.", "Created a utility function that accurately maps the generated entries to specific dates, skipping weekends or holidays as configured by the user.", "Date math can be tricky, especially when accounting for variable working days across different months.", "Python Datetime", "Ensured accurate chronological placement of logbook entries."),

    # Week 9: Mar 30 - Apr 3 (Frontend Integration)
    ("Starting the integration of the AI pipeline with the React frontend.", "Built the 'Generation Configuration' form where users input their project details, tech stack, and select the date range.", "Providing a clear, step-by-step form improves user experience when initiating a complex AI task.", "React Forms, UI Design", "Developed the main generation configuration UI."),
    ("Implementing server-sent events (SSE) or websockets for real-time generation updates.", "Configured a WebSocket connection in FastAPI to stream progress updates back to the React frontend as each day is generated.", "Long-running AI tasks require real-time feedback so the user doesn't think the application has frozen.", "WebSockets, FastAPI", "Enabled real-time progress tracking for the user."),
    ("Building the progress UI on the frontend.", "Created a sleek progress bar and a logging console component that displays messages like 'Generating Day 5...' via the WebSocket connection.", "Visual feedback is crucial for perceived performance during heavy operations.", "React UI Components", "Implemented a dynamic, real-time progress interface."),
    ("Handling the final PDF delivery.", "Updated the WebSocket protocol to send a download URL or binary blob of the final constructed PDF once the LangGraph pipeline completes.", "Transferring large PDF files requires efficient handling of binary data streams.", "Blob handling, File Download", "Users can now successfully download the AI-generated logbook."),
    ("Testing the complete end-to-end flow.", "Ran the entire process: User Input -> WebSocket -> LangGraph Planning -> Gemini Generation -> PyMuPDF construction -> Frontend Download.", "Seeing the entire system work together seamlessly is incredibly rewarding.", "End-to-End Testing", "Successfully verified the full LogiFlow generation pipeline."),

    # Week 10: Apr 6 - Apr 10 (Refining the Canvas & Manual Edits)
    ("Returning to the interactive canvas to support manual edits on *top* of the AI-generated PDF.", "Updated the frontend to load the newly generated PDF into the Konva canvas, allowing the user to review and tweak the AI's work.", "Giving users the final say and the ability to manually override AI content is a key product feature.", "React-Konva integration", "Enabled manual review and editing of generated logbooks."),
    ("Implementing a 'Save State' feature for the canvas.", "Added logic to serialize the Konva canvas state (all text nodes, positions, and properties) to a JSON object and save it to MongoDB.", "This allows users to close the browser and return to their editing session later without losing work.", "JSON Serialization, MongoDB", "Implemented session saving for the interactive canvas."),
    ("Optimizing the PDF to Image rendering.", "Modified the pdf.js implementation to use a web worker. This offloads the heavy PDF rendering from the main thread, keeping the UI responsive.", "Web workers are essential for CPU-intensive tasks in the browser to prevent UI blocking.", "Web Workers, pdf.js", "Significantly improved canvas rendering performance."),
    ("Adding 'Undo/Redo' functionality to the canvas editor.", "Implemented a history stack that records the serialized state of the canvas after every change, allowing users to step backward and forward.", "Undo/Redo is a complex but expected feature for any professional editing tool.", "State Management Algorithms", "Canvas now supports full undo/redo operations."),
    ("Refining the UI/UX of the editor.", "Added tooltips, improved the toolbar styling with a modern glassmorphism effect, and ensured the canvas is responsive to window resizing.", "Small UI polish makes the application feel like a premium, professional tool.", "CSS, Tailwind, UX Polish", "Enhanced the overall look and feel of the application."),

    # Week 11: Apr 13 - Apr 17 (Performance & Scalability)
    ("Today we focused on backend performance optimization.", "Profiled the FastAPI application using PyInstrument. Identified that the PDF rendering loop was a bottleneck and refactored it.", "Profiling tools are critical for identifying actual performance bottlenecks rather than guessing.", "PyInstrument, Profiling", "Improved PDF construction speed by 30%."),
    ("Implementing Redis for caching.", "Set up a Redis instance and integrated it with FastAPI. Cached the results of frequent, static database queries (like user preferences).", "Caching reduces database load and speeds up response times for common requests.", "Redis, Caching", "Successfully implemented an in-memory caching layer."),
    ("Load testing the AI pipeline.", "Used Locust to simulate multiple users initiating logbook generations simultaneously. Monitored server CPU and Gemini API rate limits.", "Concurrency testing reveals how the system behaves under stress and helps dimension server requirements.", "Locust, Load Testing", "Identified concurrency limits and adjusted Uvicorn worker settings."),
    ("Optimizing the Dockerfile for production.", "Switched to a multi-stage Docker build to reduce the final image size. Ensured all Python dependencies are compiled correctly.", "Smaller Docker images deploy faster and are more secure due to a reduced attack surface.", "Docker Multi-stage builds", "Reduced the application container size significantly."),
    ("Preparing the application for cloud deployment.", "Configured environment variables for production, set up logging to output to standard out, and created a render.yaml blueprint.", "Following twelve-factor app methodology ensures smooth deployment to modern cloud platforms.", "Environment Configuration", "Application is fully prepped for cloud hosting."),

    # Week 12: Apr 20 - Apr 24 (Deployment & Security)
    ("Deploying the backend to Render.", "Connected the GitHub repository to Render and deployed the FastAPI service. Configured the environment variables and secrets.", "Render's native Docker support makes deploying complex Python applications straightforward.", "Render Cloud", "Backend API successfully deployed and live."),
    ("Deploying the React frontend.", "Configured Vite to build the production assets and deployed the static site to Vercel.", "Vercel's global CDN ensures the frontend loads incredibly fast for users anywhere in the world.", "Vercel Deployment", "Frontend successfully deployed and connected to the live API."),
    ("Implementing basic authentication.", "Added JWT-based authentication to secure the backend endpoints. Users now need to log in to access their saved logbooks.", "Security is a critical requirement before launching any application to the public.", "JWT, FastAPI Security", "API is now protected by token-based authentication."),
    ("Setting up CI/CD pipelines.", "Created a GitHub Actions workflow that automatically runs linting and basic tests whenever code is pushed to the main branch.", "Continuous Integration catches errors early and automates the quality assurance process.", "GitHub Actions", "Established automated testing and deployment workflows."),
    ("Monitoring and error tracking.", "Integrated Sentry to automatically capture and report any unhandled exceptions in both the React frontend and FastAPI backend.", "Proactive error tracking is essential for maintaining reliability in a production environment.", "Sentry Integration", "Implemented robust production error monitoring."),

    # Week 13: Apr 27 - May 1 (Final Polish & Presentation Prep)
    ("Starting the final review phase.", "Conducted extensive end-to-end testing of the live deployed system. Generated a full 45-day logbook using the Gemini AI pipeline.", "Testing on the production environment often reveals edge cases missed during local development.", "QA Testing", "Verified the stability of the production system."),
    ("Writing project documentation.", "Completed the comprehensive README file, detailing the architecture, tech stack, and setup instructions for future developers.", "Good documentation is the hallmark of a professional software project.", "Markdown, Technical Writing", "Finalized all project and API documentation."),
    ("Preparing the final presentation and interview script.", "Drafted a concise pitch explaining the problem LogiFlow solves, the multi-agent AI architecture, and the tech stack used.", "Being able to clearly articulate technical decisions is just as important as writing the code.", "Presentation Prep", "Successfully synthesized the project into a compelling narrative."),
    ("Creating demo videos and screenshots.", "Recorded a screen capture of the generation process and the interactive canvas. These visual aids are crucial for the final viva.", "A live demo can fail, so having high-quality backup recordings is a necessary precaution.", "Video Recording", "Prepared all visual assets for the project demonstration."),
    ("Final Day! Project wrap-up.", "Successfully concluded the development of LogiFlow AI. The application is live, stable, and fulfilling its core objective of automating project logbooks.", "This project has significantly enhanced my skills in full-stack development and AI orchestration.", "Project Reflection", "Successfully completed the LogiFlow AI project.")
]

import os

output_path = r"c:\D\ojl\OJL-Maker\content.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("# SECTION 1\n# DAILY ACTIVITY JOURNAL\n\n")
    
    day_counter = 1
    for i, date in enumerate(valid_dates):
        if i < len(entries):
            my_space, tasks, learnings, tools, achievements = entries[i]
        else:
            my_space = "Continued refinement and bug fixing of the LogiFlow AI system."
            tasks = "Addressed minor UI bugs and improved error handling in the API."
            learnings = "Continuous maintenance is a core part of the software lifecycle."
            tools = "VS Code, Chrome DevTools"
            achievements = "Improved overall system stability."

        date_str = date.strftime("%d/%m/%Y")
        f.write(f"### DAILY ACTIVITY JOURNAL - Day {day_counter}\n")
        f.write(f"**Name:** Rupneel Maiti\n")
        f.write(f"**Date:** {date_str}\n")
        f.write(f"**Department:** B.Tech CSE (AI/ML) 25–29\n")
        f.write(f"**OJL Timing:** 3:30 PM To 6:30 PM\n")
        f.write(f"**Designation:** Software Component + Associate\n\n")
        
        f.write(f"**MY SPACE (My thoughts / My Sketch / My Notes / Things to Remember)**\n")
        f.write(f"{my_space}\n\n")
        
        f.write(f"**Tasks Carried Out Today**\n")
        f.write(f"{tasks}\n\n")
        
        f.write(f"**Key Learnings/Observations**\n")
        f.write(f"{learnings}\n\n")
        
        f.write(f"| Tools, Equipment, Technology or Techniques Used | Special Achievements |\n")
        f.write(f"| :--- | :--- |\n")
        f.write(f"| {tools} | {achievements} |\n\n")
        f.write(f"---\n\n")
        day_counter += 1

print("Logbook generated successfully with", len(valid_dates), "entries.")
