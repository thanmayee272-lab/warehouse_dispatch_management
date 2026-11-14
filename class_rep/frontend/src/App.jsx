import { useState, useEffect } from "react";
import Vote from "./components/Vote";
import Nominate from "./components/Nominate";
import Officer from "./components/Officer";
import Login from "./components/Login.jsx";
import Register from "./components/Register.jsx";

const API_URL = "http://127.0.0.1:8000";

function App() {
    const [phase, setPhase] = useState("");
    const [candidates, setCandidates] = useState([]);
    const [results, setResults] = useState(null);
    const [message, setMessage] = useState("");

    function loadAll() {
        fetch(API_URL + "/election/phase")
            .then((res) => res.json())
            .then((data) => {
                if (data.detail) {
                    setMessage(data.detail);
                } else {
                    setPhase(data.phase);

                    if (data.phase === "closed") {
                        fetch(API_URL + "/results")
                            .then((res) => res.json())
                            .then((data) => setResults(data));
                    } else {
                        setResults(null);
                    }
                }
            })
            .catch(() => setMessage("Cannot connect to server"));

        fetch(API_URL + "/candidates")
            .then((res) => res.json())
            .then((data) => {
                if (Array.isArray(data)) {
                    setCandidates(data);
                } else {
                    setMessage(data.detail);
                }
            })
            .catch(() => setMessage("Cannot connect to server"));
    }

    useEffect(() => {
        loadAll();
    }, []);

    return (
        <>
            <h1>Class Representative Election</h1>

            <hr />

            {/* Login and Register */}
            <Login />
            <Register />

            <hr />

            <h2>Election Phase: {phase}</h2>

            {message !== "" && <p>{message}</p>}

            <Vote
                apiUrl={API_URL}
                candidates={candidates}
                setMessage={setMessage}
                loadAll={loadAll}
            />

            <hr />

            <Nominate
                apiUrl={API_URL}
                candidates={candidates}
                setMessage={setMessage}
                loadAll={loadAll}
            />

            <hr />

            <Officer
                apiUrl={API_URL}
                phase={phase}
                candidates={candidates}
                results={results}
                setMessage={setMessage}
                loadAll={loadAll}
            />
        </>
    );
}

export default App;
