import streamlit as st
import base64

# --- 1. Configuration ---
st.set_page_config(
    page_title="Embedded Sudoku Game",
    layout="wide"
)

# --- 2. HTML/CSS/JS Content (Minimalist/Ocean Blue Design) ---
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minimal Sudoku</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Use Nunito font for a minimalist, clean look -->
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* --- DESIGN PALETTE --- */
        /* Primary Text: #333333 */
        /* Background: #FFFFFF */
        /* Fixed Cell Background: #F7F7F7 */
        /* Accent Color (Ocean Blue): #3B82F6 (Tailwind blue-500) */
        /* User Text: #1E40AF (Tailwind blue-800) */
        /* Error Text: #DC2626 (Tailwind red-600) */
        
        body {
            background-color: #f0f0f5; /* Very light gray background */
        }
        
        /* Ensures responsiveness and centers the app */
        .app-container {
            width: 100%;
            max-width: 500px; 
            margin: auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background-color: #FFFFFF;
            font-family: 'Nunito', sans-serif;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }
        
        h1 {
            color: #333333;
            font-weight: 800;
        }

        /* --- GRID STYLING --- */
        #sudoku-grid {
            display: grid;
            grid-template-columns: repeat(9, 1fr);
            grid-template-rows: repeat(9, 1fr);
            width: 90vmin; 
            max-width: 480px; /* Slightly smaller max-width for better spacing */
            margin: 20px auto;
            border: 2px solid #333333; /* Clean, simple outer border */
        }

        /* Cell Aspect Ratio fix */
        .cell {
            position: relative;
            width: 100%;
            padding-top: 100%; 
        }
        
        /* Input Cell Styling */
        .cell-input {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            padding: 0;
            text-align: center;
            font-size: clamp(1.5rem, 5vw, 2.5rem); 
            height: 100%;
            border: 1px solid #e0e0e0; /* Very light inner border */
            outline: none;
            background-color: #FFFFFF;
            transition: all 0.15s ease;
            font-family: 'Nunito', sans-serif;
            font-weight: 600;
            color: #333333;
        }

        /* Fixed Numbers */
        .fixed-cell {
            color: #333333; /* Dark gray for fixed numbers */
            background-color: #F7F7F7; /* Light gray background */
            font-weight: 700;
        }

        /* User-Entered Numbers */
        .user-cell {
            color: #1E40AF; /* Dark Ocean Blue */
        }

        /* Error Numbers */
        .error-cell {
            color: #DC2626; /* Muted Red */
            background-color: #FEE2E2;
        }
        
        /* Focus State (Light Blue Glow) */
        .cell-input:focus {
            box-shadow: 0 0 0 3px #93C5FD inset; /* Light blue ring */
            border-color: #3B82F6;
            z-index: 10;
            background-color: #EFF6FF; /* Very light blue background on focus */
        }

        /* --- 3x3 BLOCK LINES (Subtly thicker lines) --- */
        /* Heavy right border for the 3rd and 6th column */
        .cell:nth-child(9n+3) .cell-input {
            border-right-width: 2px !important;
            border-right-color: #333333 !important;
        }
        
        /* Heavy bottom border for the 3rd and 6th row */
        .cell:nth-child(n+19):nth-child(-n+27) .cell-input, 
        .cell:nth-child(n+46):nth-child(-n+54) .cell-input {
            border-bottom-width: 2px !important;
            border-bottom-color: #333333 !important;
        }
        
        /* Reset the borders for the 9th row */
        .cell:nth-child(n+73) .cell-input {
            border-bottom-width: 1px !important;
            border-bottom-color: #e0e0e0 !important;
        }

    </style>
</head>
<body class="bg-gray-50">

    <div class="app-container w-full max-w-xl mx-auto">
        <h1 class="text-2xl font-extrabold text-gray-800 mb-6 uppercase tracking-wider">Sudoku</h1>

        <!-- Header Status Bar -->
        <div class="w-full flex justify-between items-center px-4 py-2 mb-4 bg-white border-b-2 border-gray-100">
            <div class="text-sm font-semibold text-gray-500">
                EASY 
            </div>
            <div class="text-sm font-semibold text-gray-600 flex items-center space-x-4">
                <span class="text-red-500">MISTAKES: <span id="mistakes-counter" class="font-extrabold">0/3</span></span>
                <span>⏱️ <span id="timer" class="font-extrabold text-gray-800">00:00</span></span>
            </div>
        </div>
        
        <!-- Win/Error Message -->
        <div id="message-box" class="w-full h-8 flex items-center justify-center mb-4"></div>

        <!-- Sudoku Grid Container -->
        <div id="sudoku-grid">
            <!-- Grid content will be generated by JavaScript -->
        </div>

        <!-- Action Buttons (Responsive Layout) -->
        <div class="w-full flex flex-wrap justify-center gap-3 mt-6">
            <button id="undo-button" class="flex-1 min-w-[100px] px-4 py-3 bg-white text-gray-700 font-semibold border border-gray-300 rounded-lg transition duration-150 shadow-sm hover:shadow-md hover:bg-gray-50 disabled:opacity-50" disabled>
                Undo
            </button>
            <button id="clear-button" class="flex-1 min-w-[100px] px-4 py-3 bg-white text-gray-700 font-semibold border border-gray-300 rounded-lg transition duration-150 shadow-sm hover:shadow-md hover:bg-gray-50">
                Clear
            </button>
            <button id="solve-button" class="flex-1 min-w-[100px] px-4 py-3 bg-blue-500 text-white font-semibold rounded-lg transition duration-150 shadow-lg shadow-blue-500/30 hover:bg-blue-600 disabled:opacity-50">
                Solve
            </button>
        </div>
    </div>

    <script>
        // --- 1. GAME DATA & STATE ---
        const initialPuzzle = [
            [1, 2, 0, 7, 5, 0, 3, 0, 8],
            [4, 0, 0, 9, 0, 0, 0, 1, 8],
            [7, 8, 9, 2, 0, 0, 0, 0, 0],
            [0, 4, 8, 1, 0, 2, 7, 5, 0],
            [5, 0, 1, 3, 8, 0, 1, 3, 4],
            [0, 6, 3, 0, 1, 9, 0, 6, 0],
            [8, 1, 0, 0, 3, 4, 9, 2, 6],
            [0, 2, 0, 4, 5, 0, 0, 8, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0]
        ];
        
        let board = initialPuzzle.map(row => [...row]); // Current editable board
        const fixedCells = initialPuzzle.map(row => row.map(cell => cell !== 0)); // Fixed starting numbers
        let errorCells = new Set();
        let mistakeCount = 0;
        let boardHistory = [initialPuzzle.map(row => [...row])];
        let timerInterval;
        let seconds = 0;
        let isSolved = false;

        const gridElement = document.getElementById('sudoku-grid');
        const messageBox = document.getElementById('message-box');
        const mistakesCounter = document.getElementById('mistakes-counter');
        const undoButton = document.getElementById('undo-button');
        const clearButton = document.getElementById('clear-button');
        const solveButton = document.getElementById('solve-button');

        // --- 2. VALIDATION LOGIC ---

        function findConflicts(r, c, val) {
            const conflicts = [];
            if (val === 0) return conflicts;

            // Check Row and Column
            for (let i = 0; i < 9; i++) {
                if (i !== c && board[r][i] === val) conflicts.push(`${r},${i}`);
                if (i !== r && board[i][c] === val) conflicts.push(`${i},${c}`);
            }

            // Check 3x3 Box
            const startRow = Math.floor(r / 3) * 3;
            const startCol = Math.floor(c / 3) * 3;
            for (let i = startRow; i < startRow + 3; i++) {
                for (let j = startCol; j < startCol + 3; j++) {
                    if (i === r && j === c) continue;
                    if (board[i][j] === val) conflicts.push(`${i},${j}`);
                }
            }
            return conflicts;
        }

        function validateBoard() {
            const newErrorCells = new Set();
            let userErrorCount = 0;

            for (let r = 0; r < 9; r++) {
                for (let c = 0; c < 9; c++) {
                    const val = board[r][c];
                    if (val === 0) continue;
                    
                    const conflicts = findConflicts(r, c, val);
                    
                    if (conflicts.length > 0) {
                        newErrorCells.add(`${r},${c}`);
                        conflicts.forEach(coord => newErrorCells.add(coord));
                        
                        if (!fixedCells[r][c]) {
                            userErrorCount++;
                        }
                    }
                }
            }

            errorCells = newErrorCells;
            mistakeCount = Math.min(Math.floor(userErrorCount / 2), 3); 
            
            updateUI();
            checkWinCondition();
        }

        // --- 3. UI AND RENDERING ---

        function renderGrid() {
            gridElement.innerHTML = '';
            for (let r = 0; r < 9; r++) {
                for (let c = 0; c < 9; c++) {
                    const cellDiv = document.createElement('div');
                    cellDiv.className = 'cell'; 

                    const input = document.createElement('input');
                    input.type = 'number';
                    input.min = '1';
                    input.max = '9';
                    input.maxLength = '1';
                    input.id = `cell-${r}-${c}`;
                    input.className = 'cell-input';
                    input.dataset.row = r;
                    input.dataset.col = c;
                    
                    if (fixedCells[r][c]) {
                        input.value = board[r][c];
                        input.disabled = true;
                        input.classList.add('fixed-cell');
                    } else {
                        input.value = board[r][c] !== 0 ? board[r][c] : '';
                        input.classList.add('user-cell');
                        input.addEventListener('input', handleInputChange);
                        input.addEventListener('touchend', (e) => e.target.focus()); 
                    }

                    cellDiv.appendChild(input);
                    gridElement.appendChild(cellDiv);
                }
            }
            updateUI();
        }

        function updateUI() {
            mistakesCounter.textContent = `${mistakeCount}/3`;
            
            if (mistakeCount >= 3 && !isSolved) {
                 isSolved = true;
                 showMessage('error', 'Game Over! Too many mistakes.');
                 stopTimer();
            }
            
            undoButton.disabled = boardHistory.length <= 1 || isSolved;
            clearButton.disabled = isSolved && mistakeCount < 3;
            solveButton.disabled = isSolved;

            for (let r = 0; r < 9; r++) {
                for (let c = 0; c < 9; c++) {
                    const input = document.getElementById(`cell-${r}-${c}`);
                    if (!input) continue;

                    input.classList.remove('error-cell');
                    
                    if (errorCells.has(`${r},${c}`)) {
                        input.classList.add('error-cell');
                    }
                    
                    const val = board[r][c];
                    if (val === 0) {
                        input.value = '';
                    } else {
                        input.value = val;
                    }
                    
                    if (!fixedCells[r][c]) {
                        input.disabled = isSolved;
                    }
                }
            }
        }
        
        function showMessage(type, text) {
            let colorClass = '';
            if (type === 'success') {
                colorClass = 'bg-green-100 border-green-500 text-green-700';
            } else if (type === 'error') {
                colorClass = 'bg-red-100 border-red-500 text-red-700';
            } else {
                colorClass = 'bg-blue-100 border-blue-500 text-blue-700';
            }

            messageBox.innerHTML = `
                <div class="border px-4 py-1 rounded-lg relative w-full text-center font-bold ${colorClass} shadow-md" role="alert">
                    <span class="block sm:inline">${text}</span>
                </div>
            `;
            if (type !== 'success' && type !== 'error') {
                 setTimeout(() => messageBox.innerHTML = '', 5000);
            }
        }


        // --- 4. GAME INTERACTIONS ---

        function handleInputChange(event) {
            if (isSolved) return;

            const input = event.target;
            const r = parseInt(input.dataset.row);
            const c = parseInt(input.dataset.col);
            let val = parseInt(input.value) || 0;

            if (val < 1 || val > 9 || isNaN(val)) {
                val = 0;
            }
            
            if (board[r][c] !== val) {
                boardHistory.push(board.map(row => [...row]));
                board[r][c] = val;
                
                if (boardHistory.length > 50) {
                    boardHistory.shift(); 
                }
            }
            
            validateBoard();
        }
        
        function solvePuzzle() {
            if (isSolved) return;
            // Placeholder solver
            for (let r = 0; r < 9; r++) {
                for (let c = 0; c < 9; c++) {
                    if (board[r][c] === 0) {
                        board[r][c] = 1; 
                    }
                }
            }
            validateBoard();
            isSolved = true;
            updateUI();
            showMessage('info', 'Solver placeholder executed. Check logic yourself!');
            stopTimer();
        }

        function undoMove() {
            if (boardHistory.length > 1) {
                boardHistory.pop(); 
                board = boardHistory[boardHistory.length - 1].map(row => [...row]);
                validateBoard();
                
                if (isSolved) {
                    isSolved = false;
                    startTimer();
                }
            } else {
                showMessage('info', 'No more moves to undo.');
            }
            updateUI();
        }
        
        function clearBoard() {
            board = initialPuzzle.map(row => [...row]);
            boardHistory = [initialPuzzle.map(row => [...row])];
            errorCells.clear();
            mistakeCount = 0;
            isSolved = false;
            
            resetTimer();
            renderGrid(); 
            showMessage('info', 'Board cleared. Ready for a new attempt!');
        }

        function checkWinCondition() {
            if (mistakeCount > 0) {
                isSolved = false;
                return;
            }
            
            let isFull = true;
            for(let r=0; r<9; r++) {
                for(let c=0; c<9; c++) {
                    if (board[r][c] === 0) {
                        isFull = false;
                        break;
                    }
                }
                if (!isFull) break;
            }

            if (isFull) {
                isSolved = true;
                showMessage('success', `Congratulations! Solved in ${document.getElementById('timer').textContent}!`);
                stopTimer();
                updateUI();
            }
        }

        // --- 5. TIMER FUNCTIONS ---

        function startTimer() {
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                seconds++;
                const min = String(Math.floor(seconds / 60)).padStart(2, '0');
                const sec = String(seconds % 60).padStart(2, '0');
                document.getElementById('timer').textContent = `${min}:${sec}`;
            }, 1000);
        }

        function stopTimer() {
            clearInterval(timerInterval);
        }
        
        function resetTimer() {
             stopTimer();
             seconds = 0;
             document.getElementById('timer').textContent = '00:00';
             startTimer();
        }

        // --- 6. INITIALIZATION & EVENT LISTENERS ---

        document.addEventListener('DOMContentLoaded', () => {
            renderGrid();
            startTimer();
            
            undoButton.addEventListener('click', undoMove);
            clearButton.addEventListener('click', clearBoard);
            solveButton.addEventListener('click', solvePuzzle);
        });

    </script>
</body>
</html>
"""

# --- 3. Render Component ---
st.components.v1.html(html_content, height=800, scrolling=False)