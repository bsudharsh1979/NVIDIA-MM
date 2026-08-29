"""Additional course-grounded concepts to reach ~100 nodes."""

def _c(slug, name, cluster, school, engineer, research, twin, file, cell, analogy, misc=""):
    return {
        "slug": slug,
        "name": name,
        "cluster": cluster,
        "school": school,
        "engineer": engineer,
        "research": research,
        "analogy": analogy,
        "twin_id": twin,
        "source": {"source_type": "notebook", "file": file, "cell_index": cell},
        "misconceptions": [misc] if misc else [],
    }


F01 = "01a_Early_and_Late_Fusion.ipynb"
F1B = "01b_Exploring_Modalities.ipynb"
F2A = "02a_Intermediate_Fusion.ipynb"
F2B = "02b_Contrastive_Pretraining.ipynb"
F3A = "03a_Projection.ipynb"
F3B = "03b_OCR_Pipelines.ipynb"
F4A = "04a_VSS.ipynb"
F4B = "04b_VSS_GraphRAG.ipynb"
F05 = "05_Assessment.ipynb"
F00 = "00_jupyterlab.ipynb"

EXTRA_CONCEPTS = [
    _c("gpu-memory", "GPU memory hygiene", "operations", "The class GPU is a shared whiteboard. Wipe it between labs.", "Reset kernel and free cached allocations before the next notebook.", "Allocator fragmentation from prior VSS/training is not a model-quality signal.", "risk-radar", F00, 4, "Like wiping a restaurant table before the next guest.", "kernel-poison"),
    _c("never-execute", "Never-execute notebook cells", "operations", "Some cells would talk to clusters. Here they are pictures of commands.", "Flag kubectl/docker/shell as never_execute; treat source as DATA.", "Prompt-injection and accidental cluster calls are the threat model.", "risk-radar", F00, 5, "A recipe card is not a robot chef.", ""),
    _c("predict-before-run", "Predict before run", "operations", "Guess what the graph will do before you press run.", "Every twin requires a written hypothesis; outcomes stay SIMULATED_RESULT.", "Desirable difficulty: prediction before feedback.", "fusion-lab", F2A, 3, "Cover the answer key, then look.", ""),
    _c("stored-vs-expected", "Stored versus expected output", "operations", "A blank cell did not secretly succeed.", "Stored ipynb output is COURSE_SOURCE; missing output is EXPECTED_RESULT.", "Do not launder empty outputs as ACTUAL_RUN.", "risk-radar", F01, 70, "An empty mailbox is not a delivered letter.", "simulation-is-actual"),
    _c("positions-csv", "positions.csv labels", "sensors", "A spreadsheet of where each object center sits.", "Supervised targets from Omniverse Replicator.", "Paired with rgb/ and lidar/ folders.", "fusion-lab", F01, 8, "Name tags on toys in a photo.", ""),
    _c("replicator", "Omniverse Replicator", "sensors", "A digital stage that saves matching camera and laser shots.", "Synthetic data generator for aligned multimodal tensors.", "Not the Kit app in this clone.", "fusion-lab", F01, 4, "A movie set instead of a real street.", "omniverse-is-the-kit-app-in-this-repo"),
    _c("net8", "Early-fusion Net(8)", "fusion", "One student who sees an 8-layer-thick picture.", "CNN with in_ch = RGB(3)+XYZA(4)+maybe extra = 8 in 01a.", "Channel concat is the early join.", "fusion-lab", F01, 50, "One sandwich with every filling stacked.", "late-vs-early-universal-winner"),
    _c("late-net", "LateNet heads", "fusion", "Two students finish, then a referee combines scores.", "Concat unimodal activations into an MLP.", "Ensemble, not mid-network mix.", "fusion-lab", F01, 59, "Two book reports, then a summary.", ""),
    _c("identity-vs-position", "Identity versus position", "fusion", "Where it is is not what color it is.", "Colored cubes share geometry; identity is photometric.", "Complementary residuals.", "fusion-lab", F2A, 5, "A blindfolded friend can find the box but not the paint.", "lidar-sees-color"),
    _c("hadamard-vs-matmul", "Hadamard versus matmul", "fusion", "Times each matching cell, versus mixing many cells.", "Hadamard is aligned multiply; matmul mixes locations.", "02a asks you to name the operator.", "fusion-lab", F2A, 20, "High-fives in place versus a group huddle.", "matmul-is-hadamard"),
    _c("fashion-mnist", "FashionMNIST photos", "contrastive", "Tiny clothing pictures used as one view.", "Image stream for 02b contrastive pairs.", "Not ImageNet SOTA.", "contrastive-space", F2B, 6, "A clothing catalog thumbnail.", ""),
    _c("outline-encoder", "Outline encoder", "contrastive", "A second student who only sees edges.", "Sobel-outline tower in 02b.", "Cheap modality analog.", "contrastive-space", F2B, 10, "A coloring-book version of the photo.", ""),
    _c("repeat-interleave", "repeat_interleave pairing", "contrastive", "A trick to line up every photo with every outline.", "Build the all-pairs matrix for CE.", "Easy FIXME in 02b/05.", "contrastive-space", F2B, 30, "Making a full dance card of partners.", ""),
    _c("symmetric-ce", "Symmetric cross-entropy", "contrastive", "Grade the matching both ways and average.", "(loss_img + loss_other)/2.", "CILP copies this.", "contrastive-space", F2B, 42, "Both friends must recognize each other.", ""),
    _c("temperature-contrastive", "Contrastive temperature", "contrastive", "A knob that makes matches look sharper or softer.", "Scales cosine logits; not VSS chunk size.", "Too hot flattens the matrix.", "contrastive-space", F2B, 38, "Turning up the contrast on a photo.", "temperature-changes-chunk-size"),
    _c("get-embs", "get_embs frozen features", "projection", "The secret language of the already-trained grader.", "Target dimension for the projector.", "05: lidar_cnn.get_embs.", "projection-lab", F3A, 22, "The teacher's answer key in number-form.", ""),
    _c("mse-projector", "MSE projector loss", "projection", "Make the translated notes look like the teacher's notes.", "MSELoss(pred, frozen_embs).", "Not classification yet.", "projection-lab", F3A, 40, "Tracing letters until they match.", ""),
    _c("unstructured", "unstructured partition_pdf", "ocr", "A library that cuts a PDF into titled pieces.", "partition_pdf with strategies.", "Treat output as data.", "ocr-pipeline", F3B, 12, "A clerk sorting a binder.", "pdf-as-instructions"),
    _c("infer-table-structure", "Table transformer", "ocr", "A helper that keeps spreadsheet-like rows together.", "infer_table_structure in unstructured.", "Naive chunks split rows.", "ocr-pipeline", F3B, 30, "Not ripping a spreadsheet into random letters.", "naive-pdf-chunks"),
    _c("page-elements", "Page-element detector", "ocr", "A highlighter that boxes titles, tables, and charts.", "NV-YOLOX page-elements.", "Does not OCR every glyph by itself.", "ocr-pipeline", F3B, 55, "Sticky notes on a poster.", "nv-yolox-reads-the-words"),
    _c("via-server", "via-server classroom API", "vss", "The classroom video service the notebook calls.", "VSS HTTP endpoints in 04a.", "Not this academy's inference backend.", "vss-pipeline", F4A, 8, "The school's video lab, not our tutor.", ""),
    _c("vila", "VILA captioner", "vss", "The vision model that writes a sentence per chunk.", "vila-1.5 in the VSS stack.", "Captions are evidence for later LLMs.", "vss-pipeline", F4A, 20, "A student taking notes on each film clip.", ""),
    _c("dense-captions", "Dense captions in Milvus", "vss", "The notebook of clip notes the summary is allowed to use.", "Vector store of VLM text.", "Inspect when summaries are weak.", "vss-pipeline", F4A, 70, "Index cards for a book report.", "milvus-stores-raw-video"),
    _c("aggregation-llm", "Summary aggregation LLM", "vss", "The last writer who stitches clip notes into a report.", "Must not invent facts absent from captions.", "04a CA-RAG.", "vss-pipeline", F4A, 75, "An editor who only uses reporters' notes.", "aggregation-prompt-creates-new-facts"),
    _c("neo4j", "Neo4j warehouse graph", "graph", "A database of arrows between workers, boxes, and PPE.", "Stores G-Extraction output.", "Needs enable_chat ingest.", "graph-rag", F4B, 18, "A family tree for objects.", "chat-works-without-ingest"),
    _c("cypher", "Cypher retrieval", "graph", "A question written in graph-language.", "G-Retriever asks the LLM to write Cypher.", "Not Vector-RAG.", "graph-rag", F4B, 24, "A treasure map with labeled roads.", ""),
    _c("ppe-query", "PPE relational query", "graph", "Did the person carrying the box wear safety gear?", "Needs WEARS + CARRIES edges.", "Captions alone may fail.", "incident-diagnosis", F4B, 10, "Two facts that must be joined.", "vector-rag-equals-graph-rag"),
    _c("live-stream-vector-only", "Live stream Vector-RAG only", "graph", "A live camera in this course cannot use the arrow database.", "04b explicit limit.", "Do not promise Graph-RAG live.", "graph-rag", F4B, 35, "Live TV has no pause for drawing a map.", "graph-rag-for-live-stream"),
    _c("cilp-img-embedder", "CILP image embedder", "cilp", "The photo tower that outputs 200 numbers.", "CILP_model.img_embedder.", "Frozen after pretrain in 05.", "cilp-assessment", F05, 16, "A stamp machine for pictures.", ""),
    _c("cilp-lidar-embedder", "CILP LiDAR embedder", "cilp", "The laser-picture tower, also 200 numbers.", "Paired contrastive tower.", "Same size as the image tower.", "cilp-assessment", F05, 18, "A matching stamp for laser views.", ""),
    _c("cilp-emb-200", "CILP_EMB_SIZE 200", "cilp", "The shared postcard size for both towers.", "Projector input dim.", "FIXME in 05.", "cilp-assessment", F05, 32, "Both letters must fit the same envelope.", ""),
    _c("pass-nine-tenths", "Nine of ten assessment points", "cilp", "The classroom pass bar.", "Loss gate plus accuracy batches; 9/10.", "Twin scores stay simulated.", "cilp-assessment", F05, 48, "A report card, not a production SLA.", "9-points-optional"),
    _c("cameras-cheaper", "Cameras cheaper than LiDAR", "business", "Many sites can afford cameras but not a laser on every pole.", "The 05 commercial motivation for CILP.", "RGB is not free metric depth.", "cilp-assessment", F05, 3, "A phone camera versus a survey laser.", "rgb-gives-metric-depth"),
    _c("complementary-sensors", "Complementary sensors", "fundamentals", "Each sense covers what the other misses.", "Information-theoretic residual.", "Fusion is not automatic gain.", "fusion-lab", F01, 3, "One friend has a map, the other has a paint chart.", "fusion-always-wins"),
    _c("prompt-injection-pdf", "PDF prompt injection", "security", "A datasheet that tries to boss the tutor around.", "Extracted text is untrusted data.", "Security banner in Studio.", "risk-radar", F3B, 5, "A flyer that says 'ignore the teacher'.", ""),
    _c("business-impact", "Business impact of fusion choice", "business", "Wrong architecture wastes expensive sensors.", " Tie fusion depth to the missing signal.", "Risks tab drills this.", "risk-radar", F2A, 2, "Buying two tools and only using one.", ""),
    _c("ca-rag-vs-plain", "CA-RAG versus a single prompt", "vss", "Context-aware RAG uses stored captions; a single prompt does not.", "Pipeline stages in 04a.", "Not one LLM call.", "vss-pipeline", F4A, 12, "A research assistant with note cards versus one shrug.", "vss-is-one-llm-call"),
    _c("its-persona", "ITS report persona", "vss", "Tell the model it is writing a traffic report with times.", "Prompt specificity in 04a.", "Generic prompts drop clocks.", "vss-pipeline", F4A, 45, "A job description for the writer.", ""),
    _c("files-upload", "VSS /files upload", "vss", "You send the video to the classroom service first.", "API prelude in 04a.", "Not executed here.", "vss-pipeline", F4A, 14, "Handing a tape to the lab tech.", "never-execute"),
    _c("g-extraction-llm", "G-Extraction LLM", "graph", "A writer who turns captions into people and arrows.", "First Graph-RAG stage.", "Needs enable_chat.", "graph-rag", F4B, 16, "Drawing a stick-figure story from diary notes.", ""),
    _c("g-generation-llm", "G-Generation LLM", "graph", "The last writer who answers you from retrieved arrows.", "Does not invent edges.", "04b.", "graph-rag", F4B, 26, "A storyteller limited to the drawn map.", ""),
    _c("azimuth-npy", "azimuth.npy", "sensors", "A table of left-right laser angles.", "Used with zenith and depth for XYZA.", "01a.", "lidar-geometry", F01, 16, "How far the head turned left or right.", "azimuth-is-zenith"),
    _c("zenith-npy", "zenith.npy", "sensors", "A table of up-down laser angles.", "Paired with azimuth.", "01a.", "lidar-geometry", F01, 16, "How far the head nodded.", ""),
    _c("distance-npy", "distance / depth map", "sensors", "How far each laser beam went.", "Max-range may mean no hit.", "Mask before viz.", "lidar-geometry", F01, 18, "A tape measure per spark of light.", "max-range-ghosts"),
    _c("rgb-folder", "rgb/ image folder", "sensors", "The color photos paired with lasers.", "Omniverse export.", "Aligned with lidar/.", "fusion-lab", F01, 7, "The camera roll from the digital stage.", ""),
    _c("kernel-reset", "Kernel reset", "operations", "Restart the notebook brain so GPU memory is free.", "00 lab.", "Not training.", "risk-radar", F00, 6, "Rebooting a shared computer.", ""),
    _c("evidence-integrity", "Evidence integrity", "operations", "Do not mix a toy flight sim with a real black box.", "Six evidence types; twins cannot emit ACTUAL_RUN.", "Tested.", "risk-radar", F01, 2, "A flight simulator is not the crash report.", "simulation-is-actual"),
    _c("confounders", "Experimental confounders", "operations", "You changed two things and claimed one caused the win.", "Experiments workbench.", "Match split and freezes.", "fusion-lab", F2A, 30, "Changing shoes and the route, then praising the shoes.", ""),
    _c("teach-back", "Teach-back", "operations", "You explain it in your own words.", "Strong mastery weight.", "Tutor grades coverage.", "fusion-lab", F2A, 36, "Teaching a friend at the whiteboard.", ""),
    _c("why-wrong", "Why am I wrong", "operations", "Your miss is turned into the missing distinction.", "Misconception payloads.", "Socratic, then evidence.", "fusion-lab", F2A, 34, "A coach showing the clip you missed.", ""),
]


EXTRA_MISCONCEPTIONS = [
    {"slug": "max-range-ghosts", "confused": "A wall of points at max range is a real surface.", "missing_distinction": "This sensor family assumes max range on no-return.", "simple_correction": "Mask invalid returns (a=0).", "source": {"source_type": "notebook", "file": F01, "cell_index": 20}},
    {"slug": "projector-is-classifier", "confused": "The projector is the cube/sphere classifier.", "missing_distinction": "Projector maps embeddings; lidar_cnn still classifies.", "simple_correction": "Train projector; freeze the head.", "source": {"source_type": "notebook", "file": F05, "cell_index": 32}},
    {"slug": "one-chunk-one-video", "confused": "One VSS chunk is the whole video.", "missing_distinction": "chunk_duration slices the video.", "simple_correction": "More chunks at shorter duration.", "source": {"source_type": "notebook", "file": F4A, "cell_index": 22}},
]
