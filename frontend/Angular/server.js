
const jsonServer = require('json-server');
const server = jsonServer.create();
const router = jsonServer.router('db.json');
const middlewares = jsonServer.defaults();

// Configuration
const port = 3000;

// Middleware pour logger les requêtes
server.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

// Middleware CORS
server.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Middlewares par défaut
server.use(middlewares);

// Parse body
server.use(jsonServer.bodyParser);

// ====================================
// ROUTES PERSONNALISÉES
// ====================================


server.post('/login', (req, res) => {
  const { email, password } = req.body;
  const db = router.db;
  
  console.log(' Tentative de connexion:', email);
  
  // Chercher l'utilisateur
  const user = db.get('users').find({ email: email }).value();
  
  if (!user) {
    console.log(' Utilisateur non trouvé:', email);
    return res.status(401).json({ 
      error: 'Email ou mot de passe incorrect',
      message: 'Utilisateur non trouvé'
    });
  }
  
  console.log(' Utilisateur trouvé:', user.email, '-', user.role);
  
  // Vérifier le mot de passe
if (user.password !== password) {
  console.log(' Mot de passe incorrect pour:', email);
  return res.status(401).json({ 
    error: 'Email ou mot de passe incorrect',
    message: 'Mot de passe invalide'
  });
}

console.log(' Mot de passe validé pour:', user.email);

// Générer un faux token JWT
const token = Buffer.from(JSON.stringify({
  id: user.id,
  email: user.email,
  role: user.role,
  exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60)  // ✅ CORRECTION : en SECONDES
})).toString('base64');

// Retourner la réponse
const userResponse = {
  id: user.id,
  email: user.email,
  firstName: user.firstName,
  lastName: user.lastName,
  role: user.role,
  company: user.company,
  phone: user.phone,
  department: user.department,
  avatar: user.avatar,
  loginDate: new Date().toISOString()
};

console.log('Connexion réussie pour:', userResponse.email);

res.json({
  token: token,
  user: userResponse,
  expiresIn: 86400
});
});
//******
// Route REGISTER (sans /auth/ pour compatibilité avec auth.service.ts)
server.post('/register', (req, res) => {
  const { email, firstName, lastName, company, phone, industry, password } = req.body;
  const db = router.db;
  
  console.log('Tentative d\'inscription:', email);
  
  // Vérifier si l'email existe déjà
  const existingUser = db.get('users').find({ email: email }).value();
  
  if (existingUser) {
    console.log(' Email déjà utilisé:', email);
    return res.status(400).json({ 
      error: 'Cet email est déjà utilisé',
      message: 'Email déjà enregistré'
    });
  }
  
  // Créer le nouvel utilisateur
const newUser = {
  id: 'user_' + Date.now(),
  email: email,
  password: password,
  firstName: firstName,
  lastName: lastName,
  role: req.body.role,
  company: company,
  phone: phone || '',
  department: industry || 'Production',
  avatar: `https://ui-avatars.com/api/?name=${firstName}+${lastName}&background=2563eb&color=fff`,
  loginDate: new Date().toISOString(),
  createdAt: new Date().toISOString()
};

// ====================================
// Route LOGOUT
// ====================================

  
  // Ajouter à la base de données
  db.get('users').push(newUser).write();
  
  console.log('Nouvel utilisateur créé:', newUser.email, '-', newUser.role);
  // Générer un token
const token = Buffer.from(JSON.stringify({
  id: newUser.id,
  email: newUser.email,
  role: newUser.role,
  exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60)  // ✅ CORRECTION : en SECONDES
})).toString('base64');
  
  // Retourner la réponse
  const userResponse = {
    id: newUser.id,
    email: newUser.email,
    firstName: newUser.firstName,
    lastName: newUser.lastName,
    role: newUser.role,
    company: newUser.company,
    phone: newUser.phone,
    department: newUser.department,
    avatar: newUser.avatar,
    loginDate: newUser.loginDate
  };
  
  res.status(201).json({
    token: token,
    user: userResponse,
    expiresIn: 86400
  });
});


// Route pour obtenir l'utilisateur courant
server.get('/me', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader) {
    return res.status(401).json({ error: 'Token manquant' });
  }
  
  try {
    const token = authHeader.replace('Bearer ', '');
    const decoded = JSON.parse(Buffer.from(token, 'base64').toString());
    
    const db = router.db;
    const user = db.get('users').find({ id: decoded.id }).value();
    
    if (!user) {
      return res.status(404).json({ error: 'Utilisateur non trouvé' });
    }
    
    const userResponse = {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      role: user.role,
      company: user.company,
      phone: user.phone,
      department: user.department,
      avatar: user.avatar
    };
    
    res.json(userResponse);
  } catch (error) {
    res.status(401).json({ error: 'Token invalide' });
  }
});

// ====================================
// ROUTES STANDARDS JSON-SERVER
// ====================================
server.use('/api', router);

// Démarrer le serveur
server.listen(port, () => {

  console.log('╔═══════════════════════════════════════════════════════════╗');
  console.log('║       🏭 MOCK API SMARTFACTORY DÉMARRÉE 🏭               ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`📡 Serveur: http://localhost:${port}`);
  console.log('');
  console.log('Endpoints Auth (SANS /auth prefix):');
  console.log(`   ✅ POST http://localhost:${port}/login`);
  console.log(`   ✅ POST http://localhost:${port}/register`);
  
  console.log(`   ✅ GET  http://localhost:${port}/me`);
  console.log('');
  console.log('📊 Endpoints Ressources:');
  console.log(`   - GET  http://localhost:${port}/api/users`);
  console.log(`   - GET  http://localhost:${port}/api/employees`);
  console.log(`   - GET  http://localhost:${port}/api/machines`);
  console.log(`   - GET  http://localhost:${port}/api/production`);
  console.log(`   - GET  http://localhost:${port}/api/notifications`);
  console.log(`   - GET  http://localhost:${port}/api/reports`);
  console.log(`   - GET  http://localhost:${port}/api/kpis`);
  console.log('');
  console.log('💡 Comptes de démonstration:');
  console.log('   👤 Admin:    admin@smartfactory.tn'   ,'mdp :admin123');
  console.log('   👤 Manager:  manager@smartfactory.tn','mdp :manager123');
  console.log('   👤 Operator: operator@smartfactory.tn','mdp :operator123');
  console.log('════════════════════════════════════════════════════════════');
 
});