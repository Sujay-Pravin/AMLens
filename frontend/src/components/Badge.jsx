function Badge({ level }) {
  return <span className={`badge ${level}`}>{level}</span>;
}

export default Badge;
