import { useState } from "react";

const POSITIONS = ["class_rep", "sports_secretary", "cultural_secretary", "tech_secretary"];

function Vote({ apiUrl, candidates, setMessage, loadAll }) {
  const [roll, setRoll] = useState("");
  const [currentRoll, setCurrentRoll] = useState("");
  const [votedPositions, setVotedPositions] = useState([]);
  const [selected, setSelected] = useState(null);

  function showVoted() {
    if (roll === "") {
      setMessage("Enter roll number");
      return;
    }
    fetch(apiUrl + "/votes/" + roll + "/positions")
      .then(res => res.json())
      .then(data => {
        if (data.detail) {
          setMessage(data.detail);
        } else {
          setVotedPositions(data.voted_positions);
          setCurrentRoll(roll);
        }
      });
  }

  function readManifesto(id) {
    fetch(apiUrl + "/candidates/" + id)
      .then(res => res.json())
      .then(data => {
        setSelected(data);
      });
  }

  function vote(id) {
    if (currentRoll === "") {
      setMessage("Enter roll number first");
      return;
    }
    fetch(apiUrl + "/votes?voter_roll=" + currentRoll + "&candidate_id=" + id,
      { method: "POST" }
    )
      .then(res => res.json())
      .then(data => {
        if (data.detail) {
          setMessage(data.detail);
        } else {
          setMessage("Vote recorded successfully");
          showVoted();
          loadAll();
        }
      });
  }
  return (
    <div>
      <h3>Vote</h3>
      <input
        placeholder="Roll number"
        value={roll}
        onChange={e => setRoll(e.target.value)}
      />
      <button onClick={showVoted}>Show</button>
      {POSITIONS.map(position => (
        <div key={position}>
          <h4>{position} {votedPositions.includes(position) && "Voted"}</h4>

          {candidates.filter(c => c.position === position && c.status === "approved").map(c => (
            <p key={c.id}>
              <span onClick={() => readManifesto(c.id)}>{c.name}</span>
              <button onClick={() => vote(c.id)}>Vote</button>
            </p>
          ))}
        </div>
      ))}
      {selected !== null && (
        <p>
          <b>{selected.name}'s manifesto:</b> {selected.manifesto}
        </p>
      )}
    </div>
  );
}

export default Vote;