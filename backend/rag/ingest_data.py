"""
Maximized RAG ingestion for VisualAIze.
Run once: python -m backend.rag.ingest_data

Datasets used:
- Curated math knowledge (guaranteed quality, runs first)
- MATH Dataset (Hendrycks) - competition math + LaTeX solutions
- GSM8K - elementary reasoning chains
- GSM-Hard - harder reasoning
- DeepMind Mathematics - symbolic computation
- MathQA - structured problem solving
- ProofWiki / StackExchange - theorem explanations (via HuggingFace)
"""
from __future__ import annotations
import logging
import time
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHROMA_PATH = Path("./chroma_db")
COLLECTION_NAME = "math_knowledge"
BATCH_SIZE = 100


# ─────────────────────────────────────────────
# ChromaDB setup
# ─────────────────────────────────────────────

def _get_collection():
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def _safe_batch_add(collection, documents: List[str], metadatas: List[dict], ids: List[str]):
    """Add in batches, skip duplicates, handle errors gracefully."""
    added = 0
    for i in range(0, len(documents), BATCH_SIZE):
        batch_docs = documents[i:i+BATCH_SIZE]
        batch_meta = metadatas[i:i+BATCH_SIZE]
        batch_ids = ids[i:i+BATCH_SIZE]
        # Filter out empty docs
        filtered = [(d, m, id_) for d, m, id_ in zip(batch_docs, batch_meta, batch_ids) if d and len(d.strip()) > 20]
        if not filtered:
            continue
        docs, metas, fids = zip(*filtered)
        try:
            collection.add(documents=list(docs), metadatas=list(metas), ids=list(fids))
            added += len(docs)
        except Exception as e:
            if "already exists" in str(e).lower():
                pass  # Skip duplicates silently
            else:
                logger.warning(f"Batch add error: {e}")
    return added


# ─────────────────────────────────────────────
# 1. Curated high-quality knowledge
# ─────────────────────────────────────────────

CURATED_ENTRIES = [
    # Geometry
    {
        "content": "Pythagorean Theorem: In a right triangle with legs a, b and hypotenuse c: a^2 + b^2 = c^2.\nVisual: Three squares on sides — areas of two leg-squares sum to hypotenuse-square area.\nExamples: (3,4,5), (5,12,13), (8,15,17), (7,24,25).\nConverse: If a^2+b^2=c^2 then triangle is right-angled.\nProof approach: rearrangement of four copies of triangle inside square.\nLaTeX: a^2 + b^2 = c^2, c = \\sqrt{a^2+b^2}",
        "topic": "geometry", "difficulty": "high_school"
    },
    {
        "content": "Circle geometry: Area = πr^2, Circumference = 2πr.\nChord, secant, tangent relationships. Inscribed angle = half central angle.\nArc length = rθ for angle θ in radians. Sector area = r^2θ/2.\nEquation of circle centered at (h,k): (x-h)^2 + (y-k)^2 = r^2.\nLaTeX: A = \\pi r^2, C = 2\\pi r",
        "topic": "geometry", "difficulty": "high_school"
    },
    {
        "content": "Triangle properties: Sum of angles = 180°. Area = (1/2)base×height = (1/2)ab sin(C).\nSine rule: a/sin(A) = b/sin(B) = c/sin(C).\nCosine rule: c^2 = a^2 + b^2 - 2ab cos(C).\nHeron's formula: Area = sqrt(s(s-a)(s-b)(s-c)) where s=(a+b+c)/2.\nLaTeX: \\frac{a}{\\sin A} = \\frac{b}{\\sin B} = \\frac{c}{\\sin C}",
        "topic": "geometry", "difficulty": "high_school"
    },
    # Algebra
    {
        "content": "Quadratic Formula: For ax^2 + bx + c = 0: x = (-b ± sqrt(b^2-4ac))/(2a).\nDiscriminant D = b^2-4ac: D>0 two real roots, D=0 one root, D<0 complex roots.\nVertex form: a(x-h)^2+k where h=-b/(2a), k=c-b^2/(4a).\nFactoring: ax^2+bx+c = a(x-r1)(x-r2) where r1,r2 are roots.\nLaTeX: x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}",
        "topic": "algebra", "difficulty": "high_school"
    },
    {
        "content": "Polynomial functions: Degree n polynomial has at most n real roots.\nFactor theorem: (x-a) is factor iff f(a)=0.\nRemainder theorem: f(a) = remainder when dividing by (x-a).\nVieta's formulas: for x^2+bx+c=0, sum of roots=-b, product=c.\nBinomial theorem: (a+b)^n = sum C(n,k) a^{n-k} b^k.\nLaTeX: (a+b)^n = \\sum_{k=0}^{n} \\binom{n}{k} a^{n-k}b^k",
        "topic": "algebra", "difficulty": "high_school"
    },
    {
        "content": "Logarithms and Exponentials: log_b(x)=y iff b^y=x.\nlog(ab)=log(a)+log(b). log(a/b)=log(a)-log(b). log(a^n)=n log(a).\nChange of base: log_b(x) = ln(x)/ln(b).\nNatural log: ln(e^x)=x, e^{ln x}=x.\nExponential growth: f(t)=f(0)e^{kt}.\nLaTeX: \\log_b(x) = \\frac{\\ln x}{\\ln b}",
        "topic": "algebra", "difficulty": "high_school"
    },
    # Calculus
    {
        "content": "Derivatives: f'(x) = lim_{h→0} [f(x+h)-f(x)]/h. Measures instantaneous rate of change.\nPower rule: d/dx(x^n)=nx^{n-1}. Product rule: (fg)'=f'g+fg'.\nQuotient rule: (f/g)'=(f'g-fg')/g^2. Chain rule: d/dx[f(g(x))]=f'(g(x))g'(x).\nCommon: d/dx(sin x)=cos x, d/dx(cos x)=-sin x, d/dx(e^x)=e^x, d/dx(ln x)=1/x.\nLaTeX: f'(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}",
        "topic": "calculus", "difficulty": "undergraduate"
    },
    {
        "content": "Integration: Integral = area under curve. Antiderivative F where F'=f.\nFundamental Theorem: integral_a^b f(x)dx = F(b)-F(a).\nPower rule: integral x^n dx = x^{n+1}/(n+1)+C (n≠-1).\nSubstitution: let u=g(x), du=g'(x)dx.\nIntegration by parts: integral u dv = uv - integral v du.\nLaTeX: \\int_a^b f(x)\\,dx = F(b)-F(a)",
        "topic": "calculus", "difficulty": "undergraduate"
    },
    {
        "content": "Limits: lim_{x→a} f(x)=L means f(x)→L as x→a.\nLimit laws: sum, product, quotient of limits.\nSqueeze theorem: if g(x)≤f(x)≤h(x) and lim g=lim h=L then lim f=L.\nL'Hopital rule: if 0/0 or ∞/∞ form, lim f/g = lim f'/g'.\nKey: lim_{x→0} sin(x)/x=1, lim_{x→∞}(1+1/n)^n=e.\nLaTeX: \\lim_{x \\to a} f(x) = L",
        "topic": "calculus", "difficulty": "undergraduate"
    },
    {
        "content": "Taylor and Maclaurin Series: f(x)=sum f^{(n)}(a)/n! * (x-a)^n.\nCommon series: e^x=1+x+x^2/2!+... sin(x)=x-x^3/3!+x^5/5!-... cos(x)=1-x^2/2!+x^4/4!-...\n1/(1-x)=1+x+x^2+... for |x|<1.\nRadius of convergence: R = 1/limsup |a_n|^{1/n}.\nLaTeX: e^x = \\sum_{n=0}^{\\infty} \\frac{x^n}{n!}",
        "topic": "calculus", "difficulty": "undergraduate"
    },
    # Linear Algebra
    {
        "content": "Matrices: A (m×n) times B (n×p) = C (m×p). Not commutative: AB ≠ BA generally.\nDeterminant 2x2: det([[a,b],[c,d]])=ad-bc. det(AB)=det(A)det(B).\nInverse: A^{-1} exists iff det(A)≠0. (AB)^{-1}=B^{-1}A^{-1}.\nTranspose: (AB)^T = B^T A^T.\nTrace: sum of diagonal elements = sum of eigenvalues.\nLaTeX: \\det(A) = ad - bc",
        "topic": "linear_algebra", "difficulty": "undergraduate"
    },
    {
        "content": "Eigenvalues and Eigenvectors: Av=λv, v≠0. Characteristic equation: det(A-λI)=0.\nFor 2x2 matrix: λ^2 - trace(A)λ + det(A) = 0.\nDiagonalization: A=PDP^{-1} if A has n linearly independent eigenvectors.\nSymmetric matrices have real eigenvalues and orthogonal eigenvectors.\nPCA uses eigenvectors of covariance matrix.\nLaTeX: \\det(A - \\lambda I) = 0",
        "topic": "linear_algebra", "difficulty": "undergraduate"
    },
    # Trigonometry
    {
        "content": "Trigonometric identities: sin^2(x)+cos^2(x)=1. tan^2(x)+1=sec^2(x). 1+cot^2(x)=csc^2(x).\nDouble angle: sin(2x)=2sin(x)cos(x). cos(2x)=cos^2(x)-sin^2(x)=2cos^2(x)-1=1-2sin^2(x).\nAddition: sin(a±b)=sin(a)cos(b)±cos(a)sin(b). cos(a±b)=cos(a)cos(b)∓sin(a)sin(b).\nUnit circle key values: sin(π/6)=1/2, sin(π/4)=√2/2, sin(π/3)=√3/2.\nLaTeX: \\sin^2(x) + \\cos^2(x) = 1",
        "topic": "trigonometry", "difficulty": "high_school"
    },
    # Functions
    {
        "content": "Step Functions: Piecewise constant function. f(x)=c_i for x in [a_i, a_{i+1}).\nJump discontinuity at each step boundary: left limit ≠ right limit.\nFloor function floor(x)=greatest integer ≤ x. floor(2.7)=2, floor(-0.3)=-1.\nCeiling function ceil(x)=smallest integer ≥ x. ceil(2.1)=3.\nHeaviside: H(x)=0 for x<0, 1 for x≥0. Used in signal processing.\nLaTeX: f(x) = \\lfloor x \\rfloor",
        "topic": "functions", "difficulty": "high_school"
    },
    {
        "content": "Function transformations: f(x)+k shifts up k. f(x+h) shifts left h.\na·f(x) stretches vertically by a. f(bx) compresses horizontally by b.\nf(-x) reflects over y-axis. -f(x) reflects over x-axis.\nComposition: (f∘g)(x)=f(g(x)). Domain of f∘g: inputs of g where output is in domain of f.\nInverse: f^{-1}(f(x))=x. Graph is reflection over y=x.\nLaTeX: (f \\circ g)(x) = f(g(x))",
        "topic": "functions", "difficulty": "high_school"
    },
    # Statistics/Probability
    {
        "content": "Probability: P(A)=|A|/|S| for uniform sample space S.\nP(A∪B)=P(A)+P(B)-P(A∩B). P(A|B)=P(A∩B)/P(B).\nIndependence: P(A∩B)=P(A)P(B). Bayes: P(A|B)=P(B|A)P(A)/P(B).\nExpected value: E[X]=sum x·P(X=x). Variance: Var(X)=E[X^2]-(E[X])^2.\nLaTeX: P(A|B) = \\frac{P(B|A)P(A)}{P(B)}",
        "topic": "probability", "difficulty": "high_school"
    },
    {
        "content": "Normal Distribution: Bell curve, symmetric about mean μ. Std deviation σ.\nPDF: f(x)=(1/σ√(2π))exp(-(x-μ)^2/(2σ^2)).\n68-95-99.7 rule: 68% within 1σ, 95% within 2σ, 99.7% within 3σ.\nStandard normal Z=(X-μ)/σ. Central limit theorem: sample mean → Normal.\nLaTeX: f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}",
        "topic": "statistics", "difficulty": "undergraduate"
    },
    # Number Theory
    {
        "content": "Number theory fundamentals: Euclidean algorithm for GCD: gcd(a,b)=gcd(b, a mod b).\nBezout identity: gcd(a,b)=ax+by for some integers x,y.\nPrime factorization: every integer > 1 is product of primes uniquely.\nFermat's little theorem: a^p ≡ a (mod p) for prime p.\nChinese remainder theorem: system x≡a_i (mod n_i) has unique solution mod lcm(n_i) if n_i coprime.\nLaTeX: a^{p-1} \\equiv 1 \\pmod{p}",
        "topic": "number_theory", "difficulty": "undergraduate"
    },
    # Sequences and Series
    {
        "content": "Sequences: Arithmetic: a_n=a_1+(n-1)d. Sum_n = n(a_1+a_n)/2.\nGeometric: a_n=a_1·r^{n-1}. Sum_n = a_1(1-r^n)/(1-r).\nInfinite geometric: sum=a/(1-r) if |r|<1.\nFibonacci: F_n=F_{n-1}+F_{n-2}, F_1=F_2=1. Ratio→golden ratio φ=(1+√5)/2.\nLaTeX: S_n = \\frac{a_1(1-r^n)}{1-r}",
        "topic": "sequences", "difficulty": "high_school"
    },
    # Complex Numbers
    {
        "content": "Complex numbers: z=a+bi, i^2=-1. |z|=sqrt(a^2+b^2). arg(z)=arctan(b/a).\nEuler formula: e^{iθ}=cos(θ)+i sin(θ). e^{iπ}+1=0 (Euler's identity).\nDe Moivre: (cos θ+i sin θ)^n = cos(nθ)+i sin(nθ).\nConjugate: z̄=a-bi. z·z̄=|z|^2. Roots of unity: e^{2πik/n} for k=0,...,n-1.\nLaTeX: e^{i\\theta} = \\cos\\theta + i\\sin\\theta",
        "topic": "complex_numbers", "difficulty": "undergraduate"
    },
    # Fourier / Analysis
    {
        "content": "Fourier Series: Decomposes periodic function f(x) into sinusoids.\nf(x)=a_0/2 + sum(a_n cos(nx) + b_n sin(nx)).\na_n=(1/π)∫_{-π}^{π} f(x)cos(nx)dx. b_n=(1/π)∫_{-π}^{π} f(x)sin(nx)dx.\nApplications: signal processing, heat equation, vibration analysis.\nLaTeX: f(x) = \\frac{a_0}{2} + \\sum_{n=1}^{\\infty}(a_n\\cos(nx)+b_n\\sin(nx))",
        "topic": "analysis", "difficulty": "undergraduate"
    },
    # ML / Transformers
    {
        "content": "Attention Mechanism: Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V.\nQ=queries, K=keys, V=values matrices. d_k=key dimension (scaling prevents vanishing gradients).\nSelf-attention: all of Q,K,V from same input sequence.\nMulti-head: h parallel attention heads concatenated and projected.\nPositional encoding: PE(pos,2i)=sin(pos/10000^{2i/d_model}).\nLaTeX: \\text{Attention}(Q,K,V)=\\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V",
        "topic": "machine_learning", "difficulty": "graduate"
    },
    # Differential Equations
    {
        "content": "Differential Equations: ODE involves function and its derivatives.\nFirst order linear: dy/dx + P(x)y = Q(x). Integrating factor μ=e^{∫P dx}.\nSeparable: dy/dx=f(x)g(y) → ∫dy/g(y) = ∫f(x)dx.\nSecond order linear homogeneous: ay''+by'+cy=0. Characteristic equation ar^2+br+c=0.\nExponential solution: y=e^{rx} if r is real root.\nLaTeX: \\frac{dy}{dx} + P(x)y = Q(x)",
        "topic": "differential_equations", "difficulty": "undergraduate"
    },
    # Combinatorics
    {
        "content": "Combinatorics: Permutations P(n,r)=n!/(n-r)!. Combinations C(n,r)=n!/(r!(n-r)!).\nPigeonhole principle: n+1 items in n boxes → some box has ≥2 items.\nInclusion-exclusion: |A∪B∪C|=|A|+|B|+|C|-|A∩B|-|A∩C|-|B∩C|+|A∩B∩C|.\nGenerating functions: encode sequences as power series coefficients.\nCatalan numbers: C_n=C(2n,n)/(n+1). Counts many combinatorial structures.\nLaTeX: \\binom{n}{r} = \\frac{n!}{r!(n-r)!}",
        "topic": "combinatorics", "difficulty": "undergraduate"
    },
    # Topology / Abstract
    {
        "content": "Graph Theory: G=(V,E). Degree of vertex = number of edges. Sum of degrees = 2|E|.\nEuler path exists iff exactly 0 or 2 vertices have odd degree.\nEuler circuit iff all vertices have even degree.\nTree: connected acyclic graph. n vertices → n-1 edges.\nPlanar graph: Euler formula V-E+F=2.\nLaTeX: V - E + F = 2",
        "topic": "graph_theory", "difficulty": "undergraduate"
    },
]


def ingest_curated(collection) -> int:
    documents = [e["content"] for e in CURATED_ENTRIES]
    metadatas = [{"source": "curated", "topic": e["topic"],
                  "difficulty": e["difficulty"], "has_latex": "1"}
                 for e in CURATED_ENTRIES]
    ids = [f"curated_{i}" for i in range(len(CURATED_ENTRIES))]
    added = _safe_batch_add(collection, documents, metadatas, ids)
    logger.info(f"Curated: added {added} entries")
    return added


# ─────────────────────────────────────────────
# 2. MATH Dataset (Hendrycks)
# ─────────────────────────────────────────────

def ingest_math_dataset(collection, max_samples: int = 4000) -> int:
    logger.info("Loading MATH dataset (Hendrycks)...")
    try:
        from datasets import load_dataset
        from tqdm import tqdm
        ds = load_dataset("hendrycks/competition_math", split="train", trust_remote_code=True)
        documents, metadatas, ids = [], [], []
        for i, item in enumerate(tqdm(ds, desc="MATH", total=min(max_samples, len(ds)))):
            if i >= max_samples:
                break
            problem = (item.get("problem") or "").strip()
            solution = (item.get("solution") or "").strip()
            level = item.get("level", "Level 3")
            subject = (item.get("type") or "general").lower().replace(" ", "_")
            if not problem or not solution:
                continue
            # Format: problem + solution condensed
            content = f"Problem: {problem[:600]}\n\nSolution approach: {solution[:800]}"
            documents.append(content)
            metadatas.append({
                "source": "MATH_dataset",
                "topic": subject,
                "difficulty": level.lower().replace(" ", "_"),
                "has_latex": "1" if "\\" in content else "0"
            })
            ids.append(f"math_{i}")
        added = _safe_batch_add(collection, documents, metadatas, ids)
        logger.info(f"MATH dataset: added {added} entries")
        return added
    except Exception as e:
        logger.error(f"MATH dataset failed: {e}")
        return 0


# ─────────────────────────────────────────────
# 3. GSM8K
# ─────────────────────────────────────────────

def ingest_gsm8k(collection, max_samples: int = 1500) -> int:
    logger.info("Loading GSM8K...")
    try:
        from datasets import load_dataset
        from tqdm import tqdm
        ds = load_dataset("gsm8k", "main", split="train")
        documents, metadatas, ids = [], [], []
        for i, item in enumerate(tqdm(ds, desc="GSM8K", total=min(max_samples, len(ds)))):
            if i >= max_samples:
                break
            question = (item.get("question") or "").strip()
            answer = (item.get("answer") or "").strip()
            if not question:
                continue
            content = f"Problem: {question}\n\nStep-by-step solution:\n{answer}"
            documents.append(content[:1200])
            metadatas.append({
                "source": "GSM8K",
                "topic": "arithmetic_reasoning",
                "difficulty": "elementary",
                "has_latex": "0"
            })
            ids.append(f"gsm8k_{i}")
        added = _safe_batch_add(collection, documents, metadatas, ids)
        logger.info(f"GSM8K: added {added} entries")
        return added
    except Exception as e:
        logger.error(f"GSM8K failed: {e}")
        return 0


# ─────────────────────────────────────────────
# 4. GSM-Hard
# ─────────────────────────────────────────────

def ingest_gsm_hard(collection, max_samples: int = 500) -> int:
    logger.info("Loading GSM-Hard...")
    try:
        from datasets import load_dataset
        from tqdm import tqdm
        ds = load_dataset("reasoning-machines/gsm-hard", split="train", trust_remote_code=True)
        documents, metadatas, ids = [], [], []
        for i, item in enumerate(tqdm(ds, desc="GSM-Hard", total=min(max_samples, len(ds)))):
            if i >= max_samples:
                break
            question = (item.get("input") or item.get("question") or "").strip()
            answer = str(item.get("target") or item.get("answer") or "").strip()
            if not question:
                continue
            content = f"Hard math problem: {question}\nAnswer: {answer}"
            documents.append(content[:1000])
            metadatas.append({
                "source": "GSM_Hard",
                "topic": "arithmetic_reasoning",
                "difficulty": "hard",
                "has_latex": "0"
            })
            ids.append(f"gsmhard_{i}")
        added = _safe_batch_add(collection, documents, metadatas, ids)
        logger.info(f"GSM-Hard: added {added} entries")
        return added
    except Exception as e:
        logger.warning(f"GSM-Hard failed (skipping): {e}")
        return 0


# ─────────────────────────────────────────────
# 5. DeepMind Mathematics
# ─────────────────────────────────────────────

def ingest_deepmind(collection, max_per_task: int = 400) -> int:
    logger.info("Loading DeepMind Mathematics...")
    try:
        from datasets import load_dataset
        from tqdm import tqdm
        subtasks = [
            ("algebra__linear_1d", "algebra"),
            ("algebra__linear_2d", "algebra"),
            ("calculus__differentiate", "calculus"),
            ("arithmetic__add_or_sub", "arithmetic"),
            ("arithmetic__mul_div", "arithmetic"),
            ("numbers__place_value", "number_theory"),
            ("polynomials__evaluate", "algebra"),
            ("polynomials__expand", "algebra"),
        ]
        total_added = 0
        for task, topic in subtasks:
            try:
                ds = load_dataset("math_dataset", task, split="train", trust_remote_code=True)
                documents, metadatas, ids = [], [], []
                for i, item in enumerate(tqdm(ds, desc=f"DM/{task}", total=max_per_task)):
                    if i >= max_per_task:
                        break
                    q = (item.get("question") or "").strip()
                    a = str(item.get("answer") or "").strip()
                    if not q:
                        continue
                    content = f"Question: {q}\nAnswer: {a}"
                    documents.append(content[:600])
                    metadatas.append({
                        "source": "DeepMind_Math",
                        "topic": topic,
                        "difficulty": "intermediate",
                        "has_latex": "0"
                    })
                    ids.append(f"dm_{task}_{i}")
                added = _safe_batch_add(collection, documents, metadatas, ids)
                total_added += added
            except Exception as e:
                logger.warning(f"Skipping DM/{task}: {e}")
        logger.info(f"DeepMind: added {total_added} total entries")
        return total_added
    except Exception as e:
        logger.error(f"DeepMind dataset failed: {e}")
        return 0


# ─────────────────────────────────────────────
# 6. MathQA
# ─────────────────────────────────────────────

def ingest_mathqa(collection, max_samples: int = 1000) -> int:
    logger.info("Loading MathQA...")
    try:
        from datasets import load_dataset
        from tqdm import tqdm
        ds = load_dataset("math_qa", split="train", trust_remote_code=True)
        documents, metadatas, ids = [], [], []
        for i, item in enumerate(tqdm(ds, desc="MathQA", total=min(max_samples, len(ds)))):
            if i >= max_samples:
                break
            problem = (item.get("Problem") or "").strip()
            rationale = (item.get("Rationale") or "").strip()
            category = (item.get("category") or "general").lower()
            if not problem:
                continue
            content = f"Problem: {problem}\n\nRationale: {rationale[:600]}"
            documents.append(content[:1000])
            metadatas.append({
                "source": "MathQA",
                "topic": category,
                "difficulty": "intermediate",
                "has_latex": "0"
            })
            ids.append(f"mathqa_{i}")
        added = _safe_batch_add(collection, documents, metadatas, ids)
        logger.info(f"MathQA: added {added} entries")
        return added
    except Exception as e:
        logger.warning(f"MathQA failed (skipping): {e}")
        return 0


# ─────────────────────────────────────────────
# 7. StackExchange Mathematics (via HuggingFace)
# ─────────────────────────────────────────────

def ingest_stackexchange_math(collection, max_samples: int = 2000) -> int:
    logger.info("Loading StackExchange Mathematics...")
    try:
        from datasets import load_dataset
        from tqdm import tqdm
        ds = load_dataset("math-stack-exchange", split="train", trust_remote_code=True)
        documents, metadatas, ids = [], [], []
        for i, item in enumerate(tqdm(ds, desc="StackExchange", total=min(max_samples, len(ds)))):
            if i >= max_samples:
                break
            question = (item.get("question") or item.get("title") or "").strip()
            answer = (item.get("answer") or item.get("answers") or "")
            if isinstance(answer, list):
                answer = answer[0] if answer else ""
            answer = str(answer).strip()
            if not question or not answer:
                continue
            content = f"Q: {question[:400]}\n\nA: {answer[:800]}"
            documents.append(content)
            metadatas.append({
                "source": "StackExchange_Math",
                "topic": "general_math",
                "difficulty": "mixed",
                "has_latex": "1" if "\\" in content else "0"
            })
            ids.append(f"se_math_{i}")
        added = _safe_batch_add(collection, documents, metadatas, ids)
        logger.info(f"StackExchange Math: added {added} entries")
        return added
    except Exception as e:
        logger.warning(f"StackExchange Math failed (skipping): {e}")
        return 0


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    start = time.time()
    logger.info("=" * 60)
    logger.info("VisualAIze RAG: Maximized Knowledge Ingestion")
    logger.info("=" * 60)

    collection = _get_collection()
    initial = collection.count()
    logger.info(f"Starting DB size: {initial} documents")

    results = {}

    # Always run curated first — fast and guaranteed quality
    results["curated"] = ingest_curated(collection)

    # HuggingFace datasets
    results["gsm8k"] = ingest_gsm8k(collection, max_samples=1500)
    results["math_dataset"] = ingest_math_dataset(collection, max_samples=4000)
    results["deepmind"] = ingest_deepmind(collection, max_per_task=400)
    results["mathqa"] = ingest_mathqa(collection, max_samples=1000)
    results["gsm_hard"] = ingest_gsm_hard(collection, max_samples=500)
    results["stackexchange"] = ingest_stackexchange_math(collection, max_samples=2000)

    final = collection.count()
    elapsed = time.time() - start

    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info(f"Time taken: {elapsed/60:.1f} minutes")
    logger.info(f"DB size: {initial} → {final} documents (+{final-initial})")
    logger.info("Per-source breakdown:")
    for source, count in results.items():
        logger.info(f"  {source}: {count}")
    logger.info("=" * 60)
    logger.info("Your RAG system is ready. Restart the server.")


if __name__ == "__main__":
    main()