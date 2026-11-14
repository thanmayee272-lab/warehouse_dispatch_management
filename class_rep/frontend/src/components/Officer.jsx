const POSITIONS = ["class_rep", "sports_secretary", "cultural_secretary", "tech_secretary"];

function Officer({ apiUrl, phase, candidates, results, setMessage, loadAll }) {

  function approve(id) {
    fetch(apiUrl + "/candidates/" + id + "/approve", { method: "PATCH" })
      .then(res => res.json())
      .then(data => {
        if (data.detail) {
          setMessage(data.detail);
        } else {
          setMessage(data.message);
          loadAll();
        }
      });
  }

  function nextPhase() {
    let newPhase = "voting";
    if (phase === "voting") {
      newPhase = "closed";
    }
    fetch(apiUrl + "/election/phase?phase=" + newPhase, { method: "PATCH" })
      .then(res => res.json())
      .then(data => {
        if (data.detail) {
          setMessage(data.detail);
        } else {
          setMessage("Phase changed to " + data.phase);
          loadAll();
        }
      });
  }
  return (
    <div>
      <h3>Election Officer</h3>
      {phase !== "closed" && (
        <button onClick={nextPhase}>Next Phase</button>
      )}
      <h4>Waiting for approval</h4>
      {candidates.filter(c => c.status === "nominated").map(c => (
        <p key={c.id}>
          {c.name} ({c.roll_no}) - {c.position}
          <button onClick={() => approve(c.id)}>Approve</button>
        </p>
      ))}
      {phase === "closed" && results !== null && (
        <div>
          <h4>Results</h4>
          {POSITIONS.map(position => (
            <div key={position}>
              <b>{position}</b>
              {results[position].candidates.map(c => (
                <p key={c.candidate_id}>
                  {c.name}: {c.votes} votes
                </p>
              ))}
              <p>
                Winner: {typeof results[position].winner === "string"
                  ? results[position].winner
                  : results[position].winner.name}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Officer;