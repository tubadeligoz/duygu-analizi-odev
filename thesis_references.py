"""Primary literature and technical sources verified on 22 November 2026."""

# Numeric citation keys are stable across the private and public Word editions.
# The papers support the theoretical discussion, never the project's measured scores.
REFERENCES = [
    ("pang2002", "B. Pang, L. Lee ve S. Vaithyanathan", 2002,
     "Thumbs up? Sentiment Classification using Machine Learning Techniques",
     "Proceedings of EMNLP 2002, ss. 79–86", "10.3115/1118693.1118704", "https://aclanthology.org/W02-1011/"),
    ("turney2002", "P. D. Turney", 2002,
     "Thumbs Up or Thumbs Down? Semantic Orientation Applied to Unsupervised Classification of Reviews",
     "Proceedings of ACL 2002, ss. 417–424", "10.3115/1073083.1073153", "https://aclanthology.org/P02-1053/"),
    ("pang2008", "B. Pang ve L. Lee", 2008, "Opinion Mining and Sentiment Analysis",
     "Foundations and Trends in Information Retrieval, 2(1–2), ss. 1–135", "10.1561/1500000011", "https://www.cs.cornell.edu/home/llee/opinion-mining-sentiment-analysis-survey"),
    ("vader2014", "C. J. Hutto ve E. Gilbert", 2014,
     "VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text",
     "Proceedings of ICWSM, 8(1), ss. 216–225", "10.1609/icwsm.v8i1.14550", "https://github.com/cjhutto/vaderSentiment"),
    ("attention2017", "A. Vaswani ve diğerleri", 2017, "Attention Is All You Need",
     "Advances in Neural Information Processing Systems, 30", "10.48550/arXiv.1706.03762", "https://arxiv.org/abs/1706.03762"),
    ("bert2019", "J. Devlin, M.-W. Chang, K. Lee ve K. Toutanova", 2019,
     "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
     "Proceedings of NAACL-HLT 2019, ss. 4171–4186", "10.18653/v1/N19-1423", "https://aclanthology.org/N19-1423/"),
    ("roberta2019", "Y. Liu ve diğerleri", 2019, "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
     "arXiv ön baskısı, arXiv:1907.11692", "10.48550/arXiv.1907.11692", "https://arxiv.org/abs/1907.11692"),
    ("xlmr2020", "A. Conneau ve diğerleri", 2020, "Unsupervised Cross-lingual Representation Learning at Scale",
     "Proceedings of ACL 2020, ss. 8440–8451", "10.18653/v1/2020.acl-main.747", "https://aclanthology.org/2020.acl-main.747/"),
    ("oflazer1994", "K. Oflazer", 1994, "Two-level Description of Turkish Morphology",
     "Literary and Linguistic Computing, 9(2), ss. 137–148", "10.1093/llc/9.2.137", "https://academic.oup.com/dsh/article-abstract/9/2/137/942916"),
    ("berturk2020", "S. Schweter", 2020, "BERTurk - BERT models for Turkish",
     "Zenodo, sürüm 1.0.0, 27 Nisan 2020, yazılım ve model kaydı", "10.5281/zenodo.3770924", "https://zenodo.org/records/3770924"),
    ("brown2020", "T. B. Brown ve diğerleri", 2020, "Language Models are Few-Shot Learners",
     "Advances in Neural Information Processing Systems, 33, ss. 1877–1901", "10.48550/arXiv.2005.14165", "https://arxiv.org/abs/2005.14165"),
    ("wei2022", "J. Wei ve diğerleri", 2022, "Finetuned Language Models Are Zero-Shot Learners",
     "International Conference on Learning Representations, ICLR 2022", "10.48550/arXiv.2109.01652", "https://arxiv.org/abs/2109.01652"),
    ("ouyang2022", "L. Ouyang ve diğerleri", 2022, "Training language models to follow instructions with human feedback",
     "Advances in Neural Information Processing Systems, 35, ss. 27730–27744", "10.48550/arXiv.2203.02155", "https://arxiv.org/abs/2203.02155"),
    ("qwen2025", "Qwen Ekibi (A. Yang ve diğerleri)", 2025, "Qwen2.5 Technical Report",
     "arXiv:2412.15115, sürüm 2, 3 Ocak 2025; ilk sürüm 19 Aralık 2024", "10.48550/arXiv.2412.15115", "https://arxiv.org/abs/2412.15115v2"),
    ("zhang2024", "W. Zhang, Y. Deng, B. Liu, S. Pan ve L. Bing", 2024,
     "Sentiment Analysis in the Era of Large Language Models: A Reality Check",
     "Findings of NAACL 2024, ss. 3881–3906", "10.18653/v1/2024.findings-naacl.246", "https://aclanthology.org/2024.findings-naacl.246/"),
    ("semeval2017", "S. Rosenthal, N. Farra ve P. Nakov", 2017, "SemEval-2017 Task 4: Sentiment Analysis in Twitter",
     "Proceedings of SemEval 2017, ss. 502–518", "10.18653/v1/S17-2088", "https://aclanthology.org/S17-2088/"),
    ("tweeteval2020", "F. Barbieri, J. Camacho-Collados, L. Espinosa Anke ve L. Neves", 2020,
     "TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification",
     "Findings of EMNLP 2020, ss. 1644–1650", "10.18653/v1/2020.findings-emnlp.148", "https://aclanthology.org/2020.findings-emnlp.148/"),
    ("trsa2023", "M. Aydoğan ve V. Kocaman", 2023,
     "TRSAv1: A new benchmark dataset for classifying user reviews on Turkish e-commerce websites",
     "Journal of Information Science, 49(6), ss. 1711–1725; ilk çevrim içi yayın 2022", "10.1177/01655515221074328", "https://journals.sagepub.com/doi/10.1177/01655515221074328"),
    ("domain2007", "J. Blitzer, M. Dredze ve F. Pereira", 2007,
     "Biographies, Bollywood, Boom-boxes and Blenders: Domain Adaptation for Sentiment Classification",
     "Proceedings of ACL 2007, ss. 440–447", "", "https://aclanthology.org/P07-1056/"),
    ("metrics2009", "M. Sokolova ve G. Lapalme", 2009,
     "A systematic analysis of performance measures for classification tasks",
     "Information Processing and Management, 45(4), ss. 427–437", "10.1016/j.ipm.2009.03.002", "https://atour.iro.umontreal.ca/rali/sites/default/files/publis/SokolovaLapalme-JIPM09.pdf"),
    ("adamw2019", "I. Loshchilov ve F. Hutter", 2019, "Decoupled Weight Decay Regularization",
     "International Conference on Learning Representations, ICLR 2019", "10.48550/arXiv.1711.05101", "https://arxiv.org/abs/1711.05101"),
    ("dodge2020", "J. Dodge, G. Ilharco, R. Schwartz, A. Farhadi, H. Hajishirzi ve N. Smith", 2020,
     "Fine-Tuning Pretrained Language Models: Weight Initializations, Data Orders, and Early Stopping",
     "arXiv ön baskısı, arXiv:2002.06305", "10.48550/arXiv.2002.06305", "https://arxiv.org/abs/2002.06305"),
    ("dror2018", "R. Dror, G. Baumer, S. Shlomov ve R. Reichart", 2018,
     "The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing",
     "Proceedings of ACL 2018, ss. 1383–1392", "10.18653/v1/P18-1128", "https://aclanthology.org/P18-1128/"),
    ("bender2018", "E. M. Bender ve B. Friedman", 2018,
     "Data Statements for Natural Language Processing: Toward Mitigating System Bias and Enabling Better Science",
     "Transactions of the Association for Computational Linguistics, 6, ss. 587–604", "10.1162/tacl_a_00041", "https://aclanthology.org/Q18-1041/"),
    ("modelcards2019", "M. Mitchell ve diğerleri", 2019, "Model Cards for Model Reporting",
     "Proceedings of FAT* 2019, ss. 220–229", "10.1145/3287560.3287596", "https://arxiv.org/abs/1810.03993"),
    ("datasheets2021", "T. Gebru ve diğerleri", 2021, "Datasheets for Datasets",
     "Communications of the ACM, 64(12), ss. 86–92", "10.1145/3458723", "https://arxiv.org/abs/1803.09010"),
    ("agreement2008", "R. Artstein ve M. Poesio", 2008,
     "Survey Article: Inter-Coder Agreement for Computational Linguistics",
     "Computational Linguistics, 34(4), ss. 555–596", "10.1162/coli.07-034-R2", "https://aclanthology.org/J08-4004/"),
    ("bertcard", "Google BERT ve Hugging Face", 2026, "bert-base-uncased model kartı ve yapılandırması",
     "Teknik kaynak; deney revizyonu 86b5e0934494bd15c9632b12f734a8a67f723594", "", "https://huggingface.co/google-bert/bert-base-uncased/tree/86b5e0934494bd15c9632b12f734a8a67f723594"),
    ("berturkcard", "dbmdz ve Hugging Face", 2026, "bert-base-turkish-cased model kartı ve yapılandırması",
     "Teknik kaynak; deney revizyonu b6e1de16c983e0f2c70664591ea3f22810072608", "", "https://huggingface.co/dbmdz/bert-base-turkish-cased/tree/b6e1de16c983e0f2c70664591ea3f22810072608"),
    ("qwencard", "Qwen Ekibi", 2026, "Qwen2.5-7B-Instruct model kartı",
     "Teknik kaynak; yerel nicemlenmiş koşumun digest bilgisi Ek A içindedir", "", "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct"),
    ("tweetcard", "Cardiff NLP", 2026, "tweet_eval sentiment veri kartı",
     "Veri kaynağı; sabit revizyon b3a375baf0f409c77e6bc7aa35102b7b3534f8be", "", "https://huggingface.co/datasets/cardiffnlp/tweet_eval/tree/b3a375baf0f409c77e6bc7aa35102b7b3534f8be"),
    ("trsacard", "M. Aydoğan", 2026, "Turkish_SentimentAnalysis_TRSAv1 veri kartı",
     "Veri kaynağı; sabit revizyon 3bda52ed2c57ac1e80ac463192cafeeae9f72213", "", "https://huggingface.co/datasets/maydogan/Turkish_SentimentAnalysis_TRSAv1/tree/3bda52ed2c57ac1e80ac463192cafeeae9f72213"),
    ("ollamadocs", "Ollama", 2026, "Chat API reference",
     "Teknik belge; üretim isteği, mesajlar ve seçenekler", "", "https://docs.ollama.com/api/chat"),
]

INDEX = {item[0]: i + 1 for i, item in enumerate(REFERENCES)}


def cite(*keys):
    return "[" + ", ".join(str(INDEX[k]) for k in keys) + "]"


def formatted(item):
    key, authors, year, title, venue, doi, url = item
    # For mutable web/model cards 2026 is the access year, not a claimed release year.
    date = "Erişim 22 Kasım 2026" if INDEX[key] >= 28 else str(year)
    return f"[{INDEX[key]}] {authors}. {date}. {title}. {venue}." + (f" DOI: {doi}." if doi else "")
