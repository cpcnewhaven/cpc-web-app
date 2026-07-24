const { Button, GlassCard, NavBar } = window.CPCDesignSystem_f4f503;
const GOLD = '#e3bd7d';

function Kicker({ children }) {
  return <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: GOLD, marginBottom: 10 }}>{children}</div>;
}

function SectionHead({ kicker, title, sub, light }) {
  return (
    <div style={{ textAlign: 'center', maxWidth: 640, margin: '0 auto 44px' }}>
      {kicker && <Kicker>{kicker}</Kicker>}
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2.1rem', fontWeight: 700, margin: '0 0 10px', color: light ? '#20303f' : '#fff' }}>{title}</h2>
      {sub && <p style={{ fontSize: '1.05rem', color: light ? '#5b6b7a' : 'rgba(255,255,255,.72)', margin: 0, lineHeight: 1.6 }}>{sub}</p>}
    </div>
  );
}

function Quote({ text, attribution }) {
  return (
    <div style={{ background: 'linear-gradient(135deg,#fbf7ee,#f4ede0)', border: '1px solid #ece2cc', borderRadius: 20, padding: '2.5rem 2.5rem', boxShadow: '0 12px 40px rgba(0,0,0,.18)', maxWidth: 780, margin: '0 auto' }}>
      <p style={{ fontFamily: 'var(--font-serif)', fontSize: '1.35rem', lineHeight: 1.7, color: '#332a1c', margin: 0, fontStyle: 'italic' }}>&ldquo;{text}&rdquo;</p>
      {attribution && <p style={{ marginTop: 16, marginBottom: 0, color: '#8a7550', fontSize: '.95rem' }}>{attribution}</p>}
    </div>
  );
}

function Person({ id, name, role }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <image-slot id={id} shape="circle" placeholder={name} style={{ width: 96, height: 96, margin: '0 auto 12px', display: 'block' }}></image-slot>
      <div style={{ fontWeight: 600, color: '#fff', fontSize: '.95rem' }}>{name}</div>
      {role && <div style={{ color: 'rgba(255,255,255,.6)', fontSize: '.82rem', marginTop: 2 }}>{role}</div>}
    </div>
  );
}

const FIVE_MARKS = [
  { title: 'Gospel-Centered', body: "Trust in the gospel makes us humble, because Christ's work to us is a gift, yet boldly confident, because it's grounded in God's power. Everything we do flows from the finished work of the cross." },
  { title: 'Missional', body: 'God promises to dwell with his people across every culture and language through the church, so we strive to be missional — open, inviting, and purposeful in showing the world who Jesus is.' },
  { title: 'Confessional', body: "We humbly submit to God's Word as it has been historically interpreted, subscribing to the Westminster Standards as our summary of faith — doctrine that is alive, not distracted by cultural fads." },
  { title: 'Sacramental', body: 'Christ is fleshed out in a worship service that follows the logic of the gospel and culminates each week in communion — friendly, worshipful, and mysterious.' },
  { title: 'Communal', body: 'Christ joined us to himself and to his church, so to be a Christian is to belong to a redeemed community — marked by loving, humble accountability and one-anothering.' },
];

const STAFF = [
  ['s1','Craig Luekens','Senior Pastor'], ['s2','Jerry Ornelas','Assistant Pastor'], ['s3','Alexis Vano','Administrative Coordinator'],
  ['s4','Alex Gonzalez','AV Director'], ['s5','Christopher Battista','Audio & IT Specialist'], ['s6','Paul Wildey','Sexton'], ['s7','Jennifer Cheng','Music Coordinator'],
];
const ELDERS = [
  ['e1','Craig Luekens','Senior Pastor'], ['e2','Rob Hawkes','Emeritus'], ['e3','George Levesque',''], ['e4','David Taylor',''],
  ['e5','Tyler Rice','Clerk'], ['e6','Josh Kebabian',''], ['e7','Peter Chuchta',''], ['e8','Alan Phillips','Emeritus'],
];
const WLB = [
  ['w1','Lisa Hawkes',''], ['w2','Diane Miller','Clerk'], ['w3','Peggy Kebabian',''], ['w4','Jennifer Cheng','Sabbatical 24–25'],
  ['w5','Meg Bogue',''], ['w6','Stacy Roney','Moderator'], ['w7','Tanilla Brown',''], ['w8','Patty Chuchta',''],
];

function LeaderGroup({ id, title, blurb, people }) {
  return (
    <div style={{ marginBottom: 56 }}>
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', color: '#fff', textAlign: 'center', margin: '0 0 8px' }}>{title}</h3>
      {blurb && <p style={{ maxWidth: 620, margin: '0 auto 30px', textAlign: 'center', color: 'rgba(255,255,255,.68)', lineHeight: 1.65 }}>{blurb}</p>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(110px,1fr))', gap: 24, maxWidth: 900, margin: '0 auto' }}>
        {people.map(([pid, name, role]) => <Person key={pid} id={pid} name={name} role={role} />)}
      </div>
    </div>
  );
}

function AboutScreen() {
  return (
    <div style={{ color: 'var(--surface-text)' }}>
      <div style={{ position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)', width: 'calc(100% - 40px)', maxWidth: 1200, zIndex: 50 }}>
        <NavBar logoText="CPC New Haven" active="About" links={[
          { label: 'Home' }, { label: 'Sundays' }, { label: 'Live' }, { label: 'About' },
          { label: 'Media' }, { label: 'Community' }, { label: 'Give' }, { label: 'Resources' },
        ]} />
      </div>

      <section style={{ position: 'relative', height: '78vh', minHeight: 480 }}>
        <image-slot id="hero" shape="rect" placeholder="Congregation gathered in worship" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}></image-slot>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(9,32,58,.35) 0%, rgba(9,32,58,.55) 55%, #0a3d75 100%)', pointerEvents: 'none' }}></div>
        <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', textAlign: 'center', padding: '0 24px 64px' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '3.2rem', fontWeight: 800, color: '#fff', margin: '0 0 16px', textShadow: '0 3px 20px rgba(0,0,0,.5)', maxWidth: 760 }}>You are welcome here</h1>
          <p style={{ fontSize: '1.15rem', color: 'rgba(255,255,255,.9)', maxWidth: 620, margin: '0 0 28px', lineHeight: 1.6 }}>A community in New Haven growing in the grace of Jesus Christ, acting as faithful witnesses, and trusting in the Holy Spirit — together.</p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button variant="primary" size="lg">Plan Your Visit</Button>
            <Button variant="glass" size="lg">Watch Live</Button>
          </div>
        </div>
      </section>

      <section style={{ padding: '80px 24px 20px', maxWidth: 1180, margin: '0 auto' }}>
        <Quote text="Though we may be more sinful than we're even willing to imagine, we are more loved in Christ than we can ever dare to hope." />
      </section>

      <section style={{ padding: '90px 24px', maxWidth: 1180, margin: '0 auto' }}>
        <SectionHead kicker="Who we are" title="Our Mission" sub="Ambitious for the glory of God" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48, alignItems: 'center' }}>
          <div>
            <p style={{ fontSize: '1.2rem', lineHeight: 1.75, color: 'rgba(255,255,255,.92)', margin: 0 }}>
              We are a church that is ambitious for the glory of God by <em style={{ color: GOLD, fontStyle: 'normal', fontWeight: 700 }}>growing</em> in the truth and grace of Jesus Christ, <em style={{ color: GOLD, fontStyle: 'normal', fontWeight: 700 }}>acting</em> as a faithful witness in the greater New Haven community and world, and <em style={{ color: GOLD, fontStyle: 'normal', fontWeight: 700 }}>trusting</em> in the grace and power of the Holy Spirit.
            </p>
            <div style={{ marginTop: 28 }}>
              <Button variant="glass">What We Believe →</Button>
            </div>
          </div>
          <image-slot id="mission" shape="rounded" radius="20" placeholder="Fellowship at CPC" style={{ width: '100%', aspectRatio: '4/3', display: 'block' }}></image-slot>
        </div>
      </section>

      <section style={{ padding: '90px 24px', maxWidth: 1180, margin: '0 auto' }}>
        <SectionHead kicker="Who we are" title="Our Total Christ Spirituality" sub="All about Christ — his work, not ours" />
        <p style={{ maxWidth: 700, margin: '-16px auto 40px', textAlign: 'center', color: 'rgba(255,255,255,.75)', lineHeight: 1.7 }}>
          We want this to be all about Christ — his work, not ours, as the basis of our relationship to God and one another, and his glory, not any popular leader, as the object of our ultimate affection. It is our desire to experience total Christ, not just one brand of Christ.
        </p>
        <Quote text="The Word was made flesh, and dwelled among us; to that flesh is joined the church, and there is made total Christ, both head and body." attribution="— St. Augustine, 5th-century pastor-theologian" />
      </section>

      <section style={{ padding: '20px 24px 90px', maxWidth: 1180, margin: '0 auto' }}>
        <SectionHead kicker="Our distinctives" title="The Five Marks" sub="Our distinctive approach to church life" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(230px,1fr))', gap: 20 }}>
          {FIVE_MARKS.map((m) => (
            <div key={m.title} style={{ background: 'rgba(255,255,255,.06)', border: '1px solid rgba(255,255,255,.1)', borderRadius: 16, padding: '28px 24px' }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', color: '#fff', margin: '0 0 10px' }}>{m.title}</h3>
              <p style={{ fontSize: '.9rem', lineHeight: 1.65, color: 'rgba(255,255,255,.7)', margin: 0 }}>{m.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section style={{ padding: '10px 24px 100px', maxWidth: 1180, margin: '0 auto' }}>
        <SectionHead kicker="Leadership" title="The People Who Serve" sub="Pastors, elders, and lay leaders who shepherd our congregation" />
        <LeaderGroup id="staff" title="Our Staff Team" people={STAFF} />
        <LeaderGroup id="elders" title="Session of Elders" blurb="Elders watch diligently over the flock, exercising government and care, visiting the sick, comforting the mourner, and setting a worthy example through their zeal to make disciples." people={ELDERS} />
        <LeaderGroup id="wlb" title="Women's Leadership Board" blurb="The WLB assists elders and pastors in making disciples through life-on-life discipleship, and plans activities for the women of the church." people={WLB} />
      </section>

      <section style={{ padding: '0 24px 100px', maxWidth: 1180, margin: '0 auto' }}>
        <SectionHead kicker="Moments" title="Life Together" sub="A few glimpses of our life as a congregation" />
        <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr 1fr', gridTemplateRows: '260px 260px', gap: 16 }}>
          <image-slot id="g1" shape="rounded" radius="20" placeholder="Worship gathering" style={{ gridRow: '1 / 3', width: '100%', height: '100%' }}></image-slot>
          <image-slot id="g2" shape="rounded" radius="20" placeholder="Sunday service" style={{ width: '100%', height: '100%' }}></image-slot>
          <image-slot id="g3" shape="rounded" radius="20" placeholder="Fellowship hall" style={{ width: '100%', height: '100%' }}></image-slot>
          <image-slot id="g4" shape="rounded" radius="20" placeholder="Community event" style={{ gridColumn: '2 / 4', width: '100%', height: '100%' }}></image-slot>
        </div>
      </section>

      <section style={{ padding: '10px 24px 110px', textAlign: 'center' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 700, color: '#fff', margin: '0 0 14px' }}>Come as you are</h2>
        <p style={{ color: 'rgba(255,255,255,.75)', maxWidth: 520, margin: '0 auto 28px', lineHeight: 1.65 }}>Everyone is truly welcomed into God's presence because there is no limit to God's grace as accomplished for us by Christ.</p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button variant="primary" size="lg">Plan Your Visit</Button>
          <Button variant="secondary" size="lg">Get in Touch</Button>
        </div>
      </section>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<AboutScreen />);
