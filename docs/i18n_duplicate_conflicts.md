# 重复 msgid 译文冲突（需人工裁定）

脚本 `scripts/_resolve_po_duplicates.py` 已自动修掉「其中一份是未翻译的英文残留」这类无争议重复。
下面列出的是**两套都是真译文但措辞不同**的情况 —— 脚本**不会**替你选，因为选错会
直接改变线上对外文案。

处理方式：在你认为正确的译文前打勾，或直接编辑对应 `locale/<lang>/LC_MESSAGES/django.po`，
然后重跑 `python -m scripts._resolve_po_duplicates`（或 polib 重编 .mo）。

## 剩余冲突：17 条 msgid

### `Customized financial solutions — e.g. Energy Management Contract (EMC) to fit your budget.`

**英文原文**

> Customized financial solutions — e.g. Energy Management Contract (EMC) to fit your budget.

**fr**

1. Solutions financières personnalisées — p.ex. Contrat de gestion de l’énergie (EMC) pour s’adapter à votre budget.
2. Solutions financières personnalisées — p. ex. Contrat de gestion d'énergie (EMC) pour s'adapter à votre budget.

**es**

1. Soluciones financieras personalizadas — p.ej. Contrato de gestión energética (EMC) para adaptarse a su presupuesto.
2. Soluciones financieras personalizadas — p. ej. Contrato de Gestión de Energía (EMC) para ajustarse a su presupuesto.

**de**

1. Maßgeschneiderte Finanzlösungen — z.B. Energie-Management-Vertrag (EMC) passend zu Ihrem Budget.
2. Maßgeschneiderte Finanzlösungen — z. B. Energiemanagementvertrag (EMC), der zu Ihrem Budget passt.

**ru**

1. Индивидуальные финансовые решения — например, Контракт на управление энергопотреблением (EMC) в соответствии с вашим бюджетом.
2. Индивидуальные финансовые решения — напр. Контракт на управление энергопотреблением (EMC) в соответствии с вашим бюджетом.

**ar**

1. حلول مالية مخصصة — مثل عقد إدارة الطاقة (EMC) لتناسب ميزانيتك.
2. حلول مالية مخصصة — مثلاً عقد إدارة الطاقة (EMC) لتناسب ميزانيتك.

### `Experienced on-site install teams ensuring safe and reliable installations worldwide.`

**英文原文**

> Experienced on-site install teams ensuring safe and reliable installations worldwide.

**fr**

1. Des équipes d’installation expérimentées sur site garantissant des installations sûres et fiables dans le monde entier.
2. Équipes d'installation sur site expérimentées garantissant des installations sûres et fiables dans le monde entier.

**es**

1. Equipos de instalación experimentados in-situ garantizando instalaciones seguras y fiables en todo el mundo.
2. Equipos de instalación en sitio experimentados que garantizan instalaciones seguras y confiables en todo el mundo.

**de**

1. Erfahrene Montageteams vor Ort, die sichere und zuverlässige Installationen weltweit gewährleisten.
2. Erfahrene Vor-Ort-Installationsteams, die sichere und zuverlässige Installationen weltweit gewährleisten.

**ru**

1. Опытные монтажные бригады на объекте, обеспечивающие безопасную и надёжную установку по всему миру.
2. Опытные монтажные команды на месте, обеспечивающие безопасный и надежный монтаж по всему миру.

**ar**

1. فرق تركيب ذات خبرة في الموقع تضمن تركيبات آمنة وموثوقة حول العالم.
2. فرق تركيب ميدانية ذوو خبرة تضمن تركيبات آمنة وموثوقة في جميع أنحاء العالم.

### `Experts providing both lighting and structural engineering designs with precision manufacturing.`

**英文原文**

> Experts providing both lighting and structural engineering designs with precision manufacturing.

**fr**

1. Des experts fournissant à la fois des conceptions d’éclairage et d’ingénierie structurelle avec une fabrication de précision.
2. Experts fournissant à la fois des conceptions d'éclairage et d'ingénierie structurelle avec une fabrication de précision.

**es**

1. Expertos que proporcionan diseños de iluminación e ingeniería estructural con fabricación de precisión.

**de**

1. Experten mit Beleuchtungs- und Struktur-Ingenieurdesigns und Präzisionsfertigung.
2. Experten, die sowohl Beleuchtungs- als auch Strukturmaschineningenieurentwürfe mit Präzisionsfertigung liefern.

**ru**

1. Эксперты, предоставляющие проекты освещения и строительных конструкций с прецизионным производством.
2. Эксперты, предоставляющие как световые, так и конструктивные инженерные проекты с точным производством.

**ar**

1. خبراء يقدمون تصاميم إضاءة وهندسة إنشائية مع تصنيع بدقة.
2. خبراء يقدمون تصاميم الإضاءة والهندسة الإنشائية مع التصنيع الدقيق.

### `From initial ideas through to detailed plans we are able to supply consultancy as part of our package.`

**英文原文**

> From initial ideas through to detailed plans we are able to supply consultancy as part of our package.

**fr**

1. Des idées initiales aux plans détaillés, nous pouvons fournir des services de consultation dans le cadre de notre offre.
2. Des idées initiales aux plans détaillés, nous pouvons fournir du conseil dans le cadre de notre offre.

**es**

1. Desde ideas iniciales hasta planes detallados, podemos proporcionar consultoría como parte de nuestro paquete.
2. Desde las ideas iniciales hasta los planes detallados, podemos ofrecer consultoría como parte de nuestro paquete.

**de**

1. Von ersten Ideen bis zu detaillierten Plänen können wir Beratung als Teil unseres Pakets anbieten.

**ru**

1. От первоначальных идей до детальных планов мы можем предоставить консалтинг как часть нашего пакета.
2. От первоначальных идей до детальных планов мы можем предоставить консультации в рамках нашего пакета.

**ar**

1. من الأفكار الأولية إلى الخطط التفصيلية، يمكننا تقديم خدمات الاستشارية كجزء من باقتنا.
2. من الأفكار الأولية إلى الخطط التفصيلية يمكننا تقديم الاستشارات كجزء من باقتنا.

### `Get in touch and our engineering team will respond with a full photometric proposal within 48 hours.`

**英文原文**

> Get in touch and our engineering team will respond with a full photometric proposal within 48 hours.

**fr**

1. Contactez-nous et notre équipe d’ingénierie vous répondra avec une proposition photométrique complète sous 48 heures.
2. Contactez-nous et notre équipe d'ingénieurs répondra avec une proposition photométrique complète sous 48 heures.

**es**

1. Contáctenos y nuestro equipo de ingeniería responderá con una propuesta fotométrica completa en 48 horas.
2. Póngase en contacto y nuestro equipo de ingeniería responderá con una propuesta fotométrica completa en 48 horas.

**de**

1. Kontaktieren Sie uns und unser Ingenieurteam wird innerhalb von 48 Stunden mit einem vollständigen fotometrischen Vorschlag antworten.
2. Kontaktieren Sie uns und unser Ingenieurteam antwortet innerhalb von 48 Stunden mit einem vollständigen photometrischen Vorschlag.

**ru**

1. Свяжитесь с нами, и наша инженерная команда ответит полным светотехническим предложением в течение 48 часов.
2. Свяжитесь с нами, и наша инженерная команда ответит с полным фотометрическим предложением в течение 48 часов.

**ar**

1. تواصل معنا وسيقوم فريقنا الهندسي بالرد باقتراح قياسي ضوئي كامل خلال 48 ساعة.
2. تواصل معنا وسيرد فريق الهندسة لدينا بمقترح ضوئي كامل خلال 48 ساعة.

### `Higher light output at farther distances through proprietary reflectors and 99% light transmission glass Fresnel lenses.`

**英文原文**

> Higher light output at farther distances through proprietary reflectors and 99% light transmission glass Fresnel lenses.

**fr**

1. Flux lumineux supérieur à des distances plus grandes grâce à des réflecteurs propriétaires et des lentilles Fresnel en verre avec 99% de transmission lumineuse.
2. Sortie lumineuse supérieure à plus grande distance grâce à des réflecteurs propriétaires et des lentilles de Fresnel en verre avec 99% de transmission lumineuse.

**es**

1. Mayor rendimiento luminoso a mayores distancias mediante reflectores propietarios y lentes Fresnel de vidrio con 99% de transmisión de luz.
2. Mayor salida de luz a mayores distancias mediante reflectores patentados y lentes de Fresnel de vidrio con 99% de transmisión de luz.

**de**

1. Höherer Lichtoutput über größere Entfernungen durch proprietäre Reflektoren und Glas-Fresnellinsen mit 99% Lichttransmission.
2. Höhere Lichtausbeute bei größeren Entfernungen durch proprietäre Reflektoren und Glas-Fresnel-Linsen mit 99% Lichtdurchlässigkeit.

**ru**

1. Более высокий световой поток на больших расстояниях благодаря запатентованным отражателям и стеклянным линзам Френеля с 99% светопропусканием.
2. Более высокий световой поток на больших расстояниях благодаря фирменным отражателям и стеклянным линзам Френеля с 99% пропусканием света.

**ar**

1. مخرجات إضاءة أعلى على مسافات أبعد من خلال العاكسات الخاصة وعدسات فرينل زجاجية بنسبة 99% نفاذية ضوئية.
2. إخراج ضوء أعلى في مسافات أبعد من خلال عاكسات مسجلة الملكية وعدسات Fresnel زجاجية بنسبة 99% لنقل الضوء.

### `Lower glare index and greater uniform luminance through advanced COB light engine technology and precision optics.`

**英文原文**

> Lower glare index and greater uniform luminance through advanced COB light engine technology and precision optics.

**fr**

1. Indice d’éblouissement réduit et luminance uniforme accrue grâce à la technologie de moteur lumineux COB avancée et à l’optique de précision.
2. Indice d'éblouissement inférieur et luminance uniforme supérieure grâce à la technologie avancée de moteur de lumière COB et à l'optique de précision.

**es**

1. Índice de deslumbramiento reducido y mayor luminancia uniforme mediante tecnología avanzada de motor de luz COB y óptica de precisión.
2. Menor índice de deslumbramiento y mayor luminancia uniforme mediante tecnología avanzada de motor de luz COB y óptica de precisión.

**de**

1. Niedrigerer Blendindex und höhere gleichmäßige Leuchtdichte durch fortschrittliche COB-Lichtmotortechnologie und Präzisionsoptik.
2. Niedrigerer Blendindex und gleichmäßigere Leuchtdichte durch fortschrittliche COB-Lichtmaschinentechnologie und Präzisionsoptik.

**ru**

1. Сниженный показатель ослепляемости и повышенная равномерность яркости благодаря передовой технологии COB-световых двигателей и прецизионной оптике.
2. Более низкий индекс ослепления и большая равномерная яркость благодаря передовой технологии COB-светового двигателя и точной оптике.

**ar**

1. مؤشر وهج منخفض وسطوع منتظم أعلى من خلال تقنية محرك إضاءة COB المتقدمة والبصريات الدقيقة.
2. مؤشر وهج أقل وإضاءة موحدة أكبر من خلال تقنية محرك ضوء COB المتقدمة والبصريات الدقيقة.

### `Our COB light engine has a lower glare index and greater uniform luminance than separated LED light engines, delivering smoother, more comfortable illumination across every surface.`

**英文原文**

> Our COB light engine has a lower glare index and greater uniform luminance than separated LED light engines, delivering smoother, more comfortable illumination across every surface.

**fr**

1. Notre moteur lumineux COB présente un indice d’éblouissement plus faible et une luminance uniforme plus grande que les moteurs lumineux LED séparés, offrant un éclairage plus doux et plus confortable sur chaque surface.
2. Notre moteur de lumière COB a un indice d'éblouissement inférieur et une luminance uniforme supérieure aux moteurs LED séparés, offrant un éclairage plus doux et plus confortable sur chaque surface.

**es**

1. Nuestro motor de luz COB tiene un índice de deslumbramiento menor y una luminancia uniforme mayor que los motores de luz LED separados, ofreciendo una iluminación más suave y cómoda en cada superficie.
2. Nuestro motor de luz COB tiene un menor índice de deslumbramiento y mayor luminancia uniforme que los motores LED separados, ofreciendo una iluminación más suave y cómoda en cada superficie.

**de**

1. Unser COB-Lichtmotor hat einen niedrigeren Blendindex und eine höhere gleichmäßige Leuchtdichte als separate LED-Lichtmotoren und liefert eine sanftere, komfortablere Beleuchtung auf jeder Oberfläche.
2. Unsere COB-Lichtmaschine hat einen niedrigeren Blendindex und eine gleichmäßigere Leuchtdichte als getrennte LED-Lichtmaschinen und liefert eine gleichmäßigere, angenehmere Beleuchtung auf jeder Oberfläche.

**ru**

1. Наш COB-световой двигатель имеет более низкий показатель ослепляемости и более высокую равномерность яркости, чем разделённые LED-двигатели, обеспечивая более мягкое и комфортное освещение на каждой поверхности.
2. Наш COB-световой двигатель имеет более низкий индекс ослепления и большую равномерную яркость, чем отдельные LED-световые двигатели, обеспечивая более плавное и комфортное освещение каждой поверхности.

**ar**

1. يتمتع محرك إضاءة COB بمؤشر وهج أقل وسطوع منتظم أعلى من محركات إضاءة LED المنفصلة، مما يوفر إضاءة أكثر نعومة وراحة على كل سطح.
2. محرك ضوء COB لديه مؤشر وهج أقل وإضاءة موحدة أكبر من محركات LED المنفصلة، مما يوفر إضاءة أكثر سلاسة وراحة على كل سطح.

### `Our LED lighting products are designed to create the greatest visual comfort while delivering the highest output at the target — Improves Human Performance.`

**英文原文**

> Our LED lighting products are designed to create the greatest visual comfort while delivering the highest output at the target — Improves Human Performance.

**fr**

1. Nos produits d’éclairage LED sont conçus pour offrir le plus grand confort visuel tout en délivrant le flux le plus élevé à la cible — Améliore les performances humaines.
2. Nos produits d'éclairage LED sont conçus pour offrir le plus grand confort visuel tout en délivrant la plus haute sortie sur la cible — Améliore les performances humaines.

**es**

1. Nuestros productos de iluminación LED están diseñados para crear el mayor confort visual mientras entregan el mayor rendimiento en el objetivo — Mejora el rendimiento humano.
2. Nuestros productos de iluminación LED están diseñados para crear el mayor confort visual mientras entregan la mayor salida en el objetivo — Mejora el rendimiento humano.

**de**

1. Unsere LED-Beleuchtungsprodukte sind so konzipiert, dass sie den größten visuellen Komfort bei höchstem Lichtoutput am Ziel bieten — Verbessert die menschliche Leistung.
2. Unsere LED-Beleuchtungsprodukte sind so konzipiert, dass sie den größtmöglichen visuellen Komfort bieten und gleichzeitig die höchste Leistung am Ziel liefern — Verbessert die menschliche Leistung.

**ru**

1. Наши продукты LED-освещения предназначены для создания максимального визуального комфорта при максимальном световом потоке — Повышение эффективности человека.
2. Наши светодиодные осветительные приборы разработаны для создания наибольшего визуального комфорта при обеспечении максимальной output на цели — Повышает производительность человека.

**ar**

1. تم تصميم منتجات إضاءة LED لدينا لتحقيق أقصى راحة بصرية مع تسليم أعلى مخرجات إضاءة في الهدف — تحسين الأداء البشري.
2. تم تصميم منتجات إضاءة LED لدينا لخلق أكبر راحة بصرية مع تقديم أعلى إخراج في الهدف — يحسن الأداء البشري.

### `Over 500+ projects delivered across 50+ countries. From professional sports venues to industrial facilities, airports and seaports — we bring first-hand knowledge and experience.`

**英文原文**

> Over 500+ projects delivered across 50+ countries. From professional sports venues to industrial facilities, airports and seaports — we bring first-hand knowledge and experience.

**fr**

1. Plus de 500 projets livrés dans plus de 50 pays. Des stades sportifs professionnels aux installations industrielles, aéroports et ports maritimes — nous apportons une connaissance et une expérience de première main.
2. Plus de 500 projets livrés dans plus de 50 pays. Des lieux sportifs professionnels aux installations industrielles, aéroports et ports maritimes — nous apportons une connaissance et une expérience directes.

**es**

1. Más de 500 proyectos entregados en más de 50 países. Desde recintos deportivos profesionales hasta instalaciones industriales, aeropuertos y puertos — aportamos conocimiento y experiencia de primera mano.
2. Más de 500 proyectos entregados en más de 50 países. Desde recintos deportivos profesionales hasta instalaciones industriales, aeropuertos y puertos marítimos — aportamos conocimiento y experiencia de primera mano.

**de**

1. Über 500+ Projekte in über 50 Ländern realisiert. Von professionellen Sportstätten bis hin zu Industrieanlagen, Flughäfen und Seehäfen — wir bringen Fachwissen und Erfahrung aus erster Hand.
2. Über 500 Projekte in über 50 Ländern geliefert. Von professionellen Sportstätten bis zu Industrieanlagen, Flughäfen und Seehäfen — wir bringen direkte Kenntnisse und Erfahrung.

**ru**

1. Более 500+ проектов реализовано более чем в 50 странах. От профессиональных спортивных объектов до промышленных предприятий, аэропортов и морских портов — мы обладаем опытом и знаниями.
2. Более 500 проектов реализовано в более чем 50 странах. От профессиональных спортивных объектов до промышленных предприятий, аэропортов и морских портов — мы привносим непосредственные знания и опыт.

**ar**

1. أكثر من 500+ مشروع تم إنجازه في أكثر من 50 دولة. من المنشآت الرياضية المهنية إلى المنشآت الصناعية والمطارات والموانئ — نقدم خبرة ومعرفة مباشرة.
2. أكثر من 500 مشروع تم تسليمه في أكثر من 50 دولة. من الأماكن الرياضية المهنية إلى المرافق الصناعية والمطارات والموانئ البحرية — نحن نقدم معرفة وخبرة مباشرة.

### `Proprietary glass achieves 99% light transmission with a Fresnel pattern to cut glare. Unlike polycarbonate lenses, our glass lens will never yellow over time.`

**英文原文**

> Proprietary glass achieves 99% light transmission with a Fresnel pattern to cut glare. Unlike polycarbonate lenses, our glass lens will never yellow over time.

**fr**

1. Le verre propriétaire atteint 99% de transmission lumineuse avec un motif Fresnel pour réduire l’éblouissement. Contrairement aux lentilles en polycarbonate, notre lentille en verre ne jaunira jamais avec le temps.
2. Le verre propriétaire atteint 99% de transmission lumineuse avec un motif Fresnel pour réduire l'éblouissement. Contrairement aux lentilles en polycarbonate, notre lentille en verre ne jaunira jamais avec le temps.

**es**

1. El vidrio propietario alcanza 99% de transmisión de luz con un patrón Fresnel para reducir el deslumbramiento. A diferencia de las lentes de policarbonato, nuestra lente de vidrio nunca se amarilleará con el tiempo.
2. El vidrio patentado logra 99% de transmisión de luz con un patrón Fresnel para reducir el deslumbramiento. A diferencia de las lentes de policarbonato, nuestra lente de vidrio nunca se amarilleará con el tiempo.

**de**

1. Proprietäres Glas erreicht 99% Lichttransmission mit einem Fresnel-Muster zur Blendungsreduzierung. Im Gegensatz zu Polycarbonatlinsen vergilbt unsere Glaslinse nie im Laufe der Zeit.
2. Proprietäres Glas erreicht 99% Lichtdurchlässigkeit mit einem Fresnel-Muster zur Blendreduzierung. Im Gegensatz zu Polycarbonat-Linsen wird unsere Glaslinse mit der Zeit niemals vergilben.

**ru**

1. Запатентованное стекло обеспечивает 99% светопропускание с узором Френеля для снижения ослепляемости. В отличие от поликарбонатных линз, наша стеклянная линза никогда не пожелтеет со временем.
2. Фирменное стекло достигает 99% пропускания света с рисунком Френеля для уменьшения ослепления. В отличие от поликарбонатных линз, наша стеклянная линза никогда не пожелтеет со временем.

**ar**

1. يحقق الزجاج الخاص نسبة نفاذية ضوئية 99% مع نمط فرينل لتقليل الوهج. على عكس عدسات البولي كربونات، عدستنا الزجاجية لن تصفر أبداً مع مرور الوقت.
2. الزجاج المسجل يحقق نسبة 99% لنقل الضوء مع نمط Fresnel لتقليل الوهج. على عكس عدسات البولي كربونات، لن تتغير عدستنا الزجاجية إلى اللون الأصفر بمرور الوقت.

### `Safeguarding your investment and ensuring long-term brilliant performance.`

**英文原文**

> Safeguarding your investment and ensuring long-term brilliant performance.

**fr**

1. Protéger votre investissement et assurer une performance brillante à long terme.
2. Protection de votre investissement et garantie d'une performance brillante à long terme.

**es**

1. Protegiendo su inversión y asegurando un rendimiento brillante a largo plazo.
2. Protección de su inversión y garantía de un rendimiento brillante a largo plazo.

**de**

1. Schutz Ihrer Investition und Gewährleistung langfristig brillanter Leistung.
2. Schutz Ihrer Investition und Gewährleistung langfristiger brillanter Leistung.

**ru**

1. Защита ваших инвестиций и обеспечение долгосрочной высокой эффективности.
2. Защита ваших инвестиций и обеспечение долгосрочной блестящей производительности.

**ar**

1. حماية استثمارك وضمان أداء متميز على المدى الطويل.
2. حماية استثمارك وضمان أداء لامع طويل الأمد.

### `Special build solutions with experts providing both lighting (Dialux) and structural engineering designs according to customer demand.`

**英文原文**

> Special build solutions with experts providing both lighting (Dialux) and structural engineering designs according to customer demand.

**fr**

1. Solutions de construction spéciales avec des experts fournissant à la fois des conceptions d’éclairage (Dialux) et d’ingénierie structurelle selon la demande du client.
2. Solutions de construction spéciales avec des experts fournissant à la fois des conceptions d'éclairage (Dialux) et d'ingénierie structurelle selon la demande du client.

**es**

1. Soluciones de construcción especial con expertos que proporcionan tanto diseños de iluminación (Dialux) como diseños de ingeniería estructural según la demanda del cliente.
2. Soluciones de construcción especiales con expertos que proporcionan diseños de iluminación (Dialux) e ingeniería estructural según la demanda del cliente.

**de**

1. Spezielle Baulösungen mit Experten, die sowohl Beleuchtungs- (Dialux) als auch Struktur-Ingenieurdesigns nach Kundenvorgabe bereitstellen.
2. Spezielle Baulösungen mit Experten, die sowohl Beleuchtungs- (Dialux) als auch Strukturmaschineningenieurentwürfe nach Kundenwunsch liefern.

**ru**

1. Специальные производственные решения с экспертами, предоставляющими как проекты освещения (Dialux), так и проектирование строительных конструкций по требованию заказчика.
2. Специальные строительные решения с экспертами, предоставляющими как световые (Dialux), так и конструктивные инженерные проекты по требованию заказчика.

**ar**

1. حلول بناء خاصة مع خبراء يقدمون تصاميم إضاءة (Dialux) وهندسة إنشائية حسب طلب العميل.
2. حلول بناء خاصة مع خبراء يقدمون تصاميم الإضاءة (Dialux) والهندسة الإنشائية حسب طلب العميل.

### `The single polished aluminum reflector directs all COB light in a uniform distribution with crisp edge cutoffs — far superior to plastic lens over multiple SMD chips.`

**英文原文**

> The single polished aluminum reflector directs all COB light in a uniform distribution with crisp edge cutoffs — far superior to plastic lens over multiple SMD chips.

**fr**

1. Le réflecteur en aluminium poli unique dirige toute la lumière COB dans une distribution uniforme avec des coupes nettes — bien supérieur aux lentilles en plastique sur puces SMD multiples.
2. Le réflecteur unique en aluminium poli dirige toute la lumière COB dans une distribution uniforme avec des coupures de bord nettes — très supérieur aux lentilles en plastique sur puces SMD multiples.

**es**

1. El reflector de aluminio pulido dirige toda la luz COB en una distribución uniforme con cortes nítidos — muy superior a las lentes de plástico sobre múltiples chips SMD.
2. El reflector único de aluminio pulido dirige toda la luz COB en una distribución uniforme con cortes de borde nítidos — muy superior a la lente de plástico sobre múltiples chips SMD.

**de**

1. Der einzelne polierte Aluminiumreflektor lenkt das gesamte COB-Licht in eine gleichmäßige Verteilung mit scharfen Kanten — weit überlegen zu Kunststofflinsen über mehrere SMD-Chips.
2. Der einzelne polierte Aluminiumreflektor richtet das gesamte COB-Licht in einer gleichmäßigen Verteilung mit scharfen Randabschnitten aus — weit überlegen gegenüber Kunststofflinsen über mehreren SMD-Chips.

**ru**

1. Один полированный алюминиевый отражатель направляет весь COB-свет в равномерное распределение с чёткими краями — значительно превосходя пластиковые линзы над множеством SMD-чипов.
2. Единый полированный алюминиевый отражатель направляет весь COB-свет в равномерном распределении с четкими границами — далеко превосходит пластиковые линзы на нескольких SMD-чипах.

**ar**

1. يوجه العاكس الألومنيوم المصقول الوحيد كل إضاءة COB في توزيع منتظم مع حواف حادة — متفوق بكثير على العدسات البلاستيكية فوق شرائح SMD متعددة.
2. يعكس الألمنيوم المصقول الفردي جميع ضوء COB في توزيع موحد مع حواف حادة — متفوق بكثير على العدسات البلاستيكية على رقائق SMD متعددة.

### `Through delivering innovative lighting solutions for recreational, high school, college and semi-professional sports venues, airports, seaports and other industrial facilities, SolarOne protects the environment, reduces energy consumption, and delivers satisfying and inspiring lighting experiences.`

**英文原文**

> Through delivering innovative lighting solutions for recreational, high school, college and semi-professional sports venues, airports, seaports and other industrial facilities, SolarOne protects the environment, reduces energy consumption, and delivers satisfying and inspiring lighting experiences.

**fr**

1. En livrant des solutions d’éclairage innovantes pour les installations sportives récréatives, les lycées, les colleges et les installations semi-professionnelles, les aéroports, les ports maritimes et autres installations industrielles, SolarOne protège l’environnement, réduit la consommation d’énergie et offre des expériences d’éclairage satisfaisantes et inspirantes.
2. En livrant des solutions d'éclairage innovantes pour les lieux de sport récréatifs, scolaires, universitaires et semi-professionnels, les aéroports, ports maritimes et autres installations industrielles, SolarOne protège l'environnement, réduit la consommation d'énergie et offre des expériences d'éclairage satisfaisantes et inspirantes.

**es**

1. Al ofrecer soluciones de iluminación innovadoras para instalaciones deportivas recreativas, escuelas secundarias, universidades e instalaciones semi-profesionales, aeropuertos, puertos y otras instalaciones industriales, SolarOne protege el medio ambiente, reduce el consumo de energía y ofrece experiencias de iluminación satisfactorias e inspiradoras.
2. Al ofrecer soluciones de iluminación innovadoras para recintos deportivos recreativos, escuelas, universidades y semi-profesionales, aeropuertos, puertos marítimos y otras instalaciones industriales, SolarOne protege el medio ambiente, reduce el consumo de energía y ofrece experiencias de iluminación satisfactorias e inspiradoras.

**de**

1. Durch die Lieferung innovativer Beleuchtungslösungen für Freizeitanlagen, High-School-, College- und Semiprofi-Sportstätten, Flughäfen, Seehäfen und andere Industrieanlagen schützt SolarOne die Umwelt, reduziert den Energieverbrauch und liefert zufriedenstellende und inspirierende Beleuchtungserlebnisse.
2. Durch die Lieferung innovativer Beleuchtungslösungen für Freizeit-, Schul-, College- und semiprofessionelle Sportstätten, Flughäfen, Seehäfen und andere industrielle Anlagen schützt SolarOne die Umwelt, reduziert den Energieverbrauch und liefert zufriedenstellende und inspirierende Beleuchtungserlebnisse.

**ru**

1. Предоставляя инновационные решения освещения для рекреационных спортивных площадок, средних школ, колледжей и полупрофессиональных спортивных объектов, аэропортов, морских портов и других промышленных предприятий, SolarOne защищает окружающую среду, снижает потребление энергии и обеспечивает приятные и вдохновляющие впечатления от освещения.
2. Предоставляя инновационные решения по освещению для рекреационных, школьных, университетских и полупрофессиональных спортивных объектов, аэропортов, морских портов и других промышленных предприятий, SolarOne защищает окружающую среду, снижает энергопотребление и обеспечивает удовлетворительный и вдохновляющий опыт освещения.

**ar**

1. من خلال تقديم حلول إضاءة مبتكرة للمنشآت الرياضية الترفيهية والمدارس الثانوية والجامعات والمنشآت شبه المهنية والمطارات والموانئ والمنشآت الصناعية الأخرى، تحمي SolarOne البيئة وتقلل استهلاك الطاقة وتوفر تجارب إضاءة مُرضية ومُلهمة.
2. من خلال تقديم حلول إضاءة مبتكرة للأماكن الرياضية الترفيهية والمدرسية والجامعية وشبه المهنية والمطارات والموانئ البحرية والمرافق الصناعية الأخرى، تحمي SolarOne البيئة وتقلل استهلاك الطاقة وتقدم تجارب إضاءة مرضية وملهمة.

### `We approach each project as a unique opportunity to exceed expectations in terms of improved lighting, visual comfort and operational savings.`

**英文原文**

> We approach each project as a unique opportunity to exceed expectations in terms of improved lighting, visual comfort and operational savings.

**fr**

1. Nous abordons chaque projet comme une opportunité unique de dépasser les attentes en matière d’éclairage amélioré, de confort visuel et d’économies opérationnelles.
2. Nous abordons chaque projet comme une opportunité unique de dépasser les attentes en matière d'éclairage amélioré, de confort visuel et d'économies opérationnelles.

**es**

1. Abordamos cada proyecto como una oportunidad única de superar las expectativas en términos de iluminación mejorada, confort visual y ahorro operativo.

**de**

1. Wir betrachten jedes Projekt als einzigartige Möglichkeit, die Erwartungen an verbesserter Beleuchtung, visuellem Komfort und betrieblichen Einsparungen zu übertreffen.
2. Wir betrachten jedes Projekt als eine einzigartige Gelegenheit, die Erwartungen in Bezug auf verbesserte Beleuchtung, visuellen Komfort und betriebliche Einsparungen zu übertreffen.

**ru**

1. Мы рассматриваем каждый проект как уникальную возможность превзойти ожидания в плане улучшения освещения, визуального комфорта и операционной экономии.
2. Мы рассматриваем каждый проект как уникальную возможность превзойти ожидания в плане улучшенного освещения, визуального комфорта и эксплуатационной экономии.

**ar**

1. نتعامل مع كل مشروع كفرصة فريدة لتجاوز التوقعات في تحسين الإضاءة والراحة البصرية وتوفير التكاليف التشغيلية.
2. نتعامل مع كل مشروع كفرصة فريدة لتجاوز التوقعات من حيث الإضاءة المحسنة والراحة البصرية والمدخرات التشغيلية.

### `We bring first-hand knowledge and experience for new and retrofit projects — from small projects requiring a few lights to professional high-level facilities, we’ve got you covered.`

**英文原文**

> We bring first-hand knowledge and experience for new and retrofit projects — from small projects requiring a few lights to professional high-level facilities, we’ve got you covered.

**fr**

1. Nous apportons des connaissances et une expérience de première main pour les projets neufs et de rénovation — des petits projets nécessitant quelques luminaires aux installations professionnelles de haut niveau, nous vous couvrons.
2. Nous apportons une connaissance et une expérience directes pour les projets neufs et de rénovation — des petits projets nécessitant quelques lumières aux installations professionnelles de haut niveau, nous couvrons tous vos besoins.

**es**

1. Aportamos conocimientos y experiencia de primera mano para proyectos nuevos y de renovación — desde pequeños proyectos que requieren pocas luminarias hasta instalaciones profesionales de alto nivel, le cubrimos.
2. Aportamos conocimiento y experiencia de primera mano para proyectos nuevos y de retrofit — desde pequeños proyectos que requieren algunas luces hasta instalaciones profesionales de alto nivel, le cubrimos.

**de**

1. Wir bringen Fachwissen und Erfahrung aus erster Hand für neue und Sanierungsprojekte — von kleinen Projekten, die wenige Leuchten benötigen, bis hin zu professionellen Hochleistungsanlagen, wir sind für Sie da.
2. Wir bringen direkte Kenntnisse und Erfahrung für Neu- und Retrofit-Projekte — von kleinen Projekten mit wenigen Leuchten bis zu professionellen Anlagen auf hohem Niveau, wir decken alles ab.

**ru**

1. Мы обладаем знаниями и опытом для новых проектов и модернизации — от небольших проектов, требующих нескольких светильников, до профессиональных объектов высокого уровня, мы вам поможем.
2. Мы привносим непосредственные знания и опыт для новых проектов и проектов модернизации — от небольших проектов, требующих нескольких светильников, до профессиональных объектов высокого уровня, мы вас охватим.

**ar**

1. نقدم خبرة ومعرفة مباشرة للمشاريع الجديدة وتجديد المشاريع — من المشاريع الصغيرة التي تتطلب بضع مصابيح إلى المنشآت المهنية عالية المستوى، نحن في خدمتكم.
2. نقدم معرفة وخبرة مباشرة للمشاريع الجديدة ومشاريع التجديد — من المشاريع الصغيرة التي تتطلب بعض الأضواء إلى المرافق المهنية عالية المستوى، نحن نغطي احتياجاتك.
