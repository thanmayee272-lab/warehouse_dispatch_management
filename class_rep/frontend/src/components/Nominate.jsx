import { useState } from "react";

function Nominate({ apiUrl, candidates, setMessage, loadAll }) {
  const [roll, setRoll] = useState("");
  const [name, setName] = useState("");
  const [position, setPosition] = useState("class_rep");
  const [manifesto, setManifesto] = useState("");
  const [withdrawRoll, setWithdrawRoll] = useState("");

  function nominate() {
    if (roll === "" || name === "" || manifesto === "") {
      setMessage("Please fill all fields");
      return;
    }
    fetch(apiUrl + "/candidates?roll_no=" + roll + "&name=" + name +
      "&position=" + position + "&manifesto=" + manifesto,
      { method: "POST" })
      .then(res => res.json())
      .then(data => {
        setMessage(data.message || data.detail);
        loadAll();
      });
  }

  function withdraw() {
    let id = null;
    for (let c of candidates) {
      if (c.roll_no === withdrawRoll && c.status !== "withdrawn") {
        id = c.id;
      }
    }
    if (id === null) {
      setMessage("Candidate not found");
      return;
    }
    fetch(apiUrl + "/candidates/" + id + "/withdraw?roll_no=" + withdrawRoll,
      { method: "PATCH" })
      .then(res => res.json())
      .then(data => {
        setMessage(data.message || data.detail);
        loadAll();
      });
  }
  return (
    <div>
      <h3>Nominate</h3>
      <input placeholder="Roll number" value={roll} onChange={e => setRoll(e.target.value)} />
      <input placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
      <select value={position} onChange={e => setPosition(e.target.value)}>
        <option value="class_rep">class_rep</option>
        <option value="sports_secretary">sports_secretary</option>
        <option value="cultural_secretary">cultural_secretary</option>
        <option value="tech_secretary">tech_secretary</option>
      </select>
      <textarea placeholder="Manifesto" value={manifesto} onChange={e => setManifesto(e.target.value)} />
      <button onClick={nominate}>Nominate</button>
      <h4>Withdraw</h4>
      <input placeholder="Roll number" value={withdrawRoll} onChange={e => setWithdrawRoll(e.target.value)} />
      <button onClick={withdraw}>Withdraw</button>
    </div>
  );
}
export default Nominate;