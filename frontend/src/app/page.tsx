// // src/app/page.tsx
// "use client"; // <-- Mark this as a Client Component

// import { useState, ChangeEvent, FormEvent } from "react";

// export default function Page() {
//   // ──────────────────────────────────────────────────────────────────────
//   // State variables
//   // ──────────────────────────────────────────────────────────────────────
//   const [url, setUrl] = useState<string>("");           // User‐entered URL
//   const [status, setStatus] = useState<string>("");     // “Scraping…”, “Error…”, “Clone ready.”
//   const [clonedHtml, setClonedHtml] = useState<string>("");   // HTML returned from backend
//   const [downloadUrl, setDownloadUrl] = useState<string>(""); // Blob URL for download

//   // ──────────────────────────────────────────────────────────────────────
//   // Handlers
//   // ──────────────────────────────────────────────────────────────────────

//   // Update `url` state as the user types
//   const handleUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
//     setUrl(e.target.value);
//   };

//   // Called when the user clicks “Clone”
//   const handleClone = async (e: FormEvent) => {
//     e.preventDefault();

//     if (!url) {
//       setStatus("Please enter a valid URL.");
//       return;
//     }

//     setStatus("Scraping & generating clone…");
//     setClonedHtml("");
//     setDownloadUrl("");

//     try {
//       // POST to /api/clone (this will be proxied to your FastAPI)
//       const response = await fetch("/api/clone", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ url }),
//       });

//       if (!response.ok) {
//         let detail = `HTTP ${response.status}`;
//         try {
//           const errJSON = await response.json();
//           if (errJSON.detail) detail = errJSON.detail;
//         } catch {}
//         throw new Error(detail);
//       }

//       const data: { html: string } = await response.json();
//       setClonedHtml(data.html);

//       // Create a Blob so user can download the HTML
//       const blob = new Blob([data.html], { type: "text/html" });
//       setDownloadUrl(URL.createObjectURL(blob));

//       setStatus("Clone ready.");
//     } catch (err: any) {
//       console.error("Error calling /api/clone:", err);
//       setStatus(`Error: ${err.message}`);
//     }
//   };

//   // ──────────────────────────────────────────────────────────────────────
//   // Render
//   // ──────────────────────────────────────────────────────────────────────
//   return (
//     <div className="min-h-screen p-8 flex flex-col items-center font-sans">
//       <h1 className="text-3xl font-bold mb-6">Website Cloner</h1>

//       {/* 1) URL input form */}
//       <form onSubmit={handleClone} className="flex gap-2 mb-4">
//         <input
//           type="url"
//           placeholder="https://example.com"
//           value={url}
//           onChange={handleUrlChange}
//           className="w-80 p-2 border border-gray-300 rounded"
//         />
//         <button
//           type="submit"
//           disabled={status.startsWith("Scraping")}
//           className={`px-4 py-2 bg-blue-600 text-white rounded ${
//             status.startsWith("Scraping")
//               ? "opacity-50 cursor-not-allowed"
//               : "hover:bg-blue-700"
//           }`}
//         >
//           {status.startsWith("Scraping") ? "Loading…" : "Clone"}
//         </button>
//       </form>

//       {/* 2) Status message */}
//       {status && <p className="italic text-gray-600 mb-4">{status}</p>}

//       {/* 3) Download link & iframe preview */}
//       {clonedHtml && (
//         <div className="w-full max-w-4xl">
//           <a
//             href={downloadUrl}
//             download="cloned.html"
//             className="inline-block mb-4 text-blue-600 hover:underline"
//           >
//             Download Cloned HTML
//           </a>
//           <div className="border border-gray-300">
//             <iframe
//               srcDoc={clonedHtml}
//               title="Cloned Preview"
//               className="w-full h-[500px]"
//             />
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }



// src/app/page.tsx
// app/page.tsx
"use client";

import { useState, ChangeEvent, FormEvent } from "react";

export default function Page() {
  // ──────────────────────────────────────────────────────────────────────
  // State variables
  // ──────────────────────────────────────────────────────────────────────
  const [url, setUrl] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [clonedHtml, setClonedHtml] = useState<string>("");
  const [downloadUrl, setDownloadUrl] = useState<string>("");
  const [activeTab, setActiveTab] = useState<string>("Landing Pages");

  // ──────────────────────────────────────────────────────────────────────
  // Handlers (unchanged)
  // ──────────────────────────────────────────────────────────────────────
  const handleUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
  };

  const handleClone = async (e: FormEvent) => {
    e.preventDefault();
    if (!url) {
      setStatus("Please enter a valid URL.");
      return;
    }

    setStatus("Scraping & generating clone…");
    setClonedHtml("");
    setDownloadUrl("");

    try {
      const response = await fetch("/api/clone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const errJSON = await response.json();
          if (errJSON.detail) detail = errJSON.detail;
        } catch {}
        throw new Error(detail);
      }

      const data: { html: string } = await response.json();
      setClonedHtml(data.html);

      const blob = new Blob([data.html], { type: "text/html" });
      setDownloadUrl(URL.createObjectURL(blob));

      setStatus("Clone ready.");
    } catch (err: any) {
      console.error("Error calling /api/clone:", err);
      setStatus(`Error: ${err.message}`);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleClone(e as any);
    }
  };

  // ──────────────────────────────────────────────────────────────────────
  // Render
  // ──────────────────────────────────────────────────────────────────────
  return (
    <main className="flex flex-col items-center px-4 md:px-8 pt-8 pb-8">
      {/** ─────────────────────────────────────────────────────────────── **/}
      {/** Hero Section (shrunk) **/}
      {/** ─────────────────────────────────────────────────────────────── **/}
      <div className="text-center mb-8">
        {/** Smaller Hero Logo container **/}
        <div className="w-12 h-12 flex items-center justify-center mb-4 mx-auto orchid-bloom">
          <svg
            width="48"
            height="48"
            viewBox="0 0 64 64"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <ellipse cx="32" cy="16" rx="16" ry="16" fill="#E879F9" />
            <ellipse cx="32" cy="48" rx="16" ry="16" fill="#E879F9" />
            <ellipse cx="16" cy="32" rx="16" ry="16" fill="#E879F9" />
            <ellipse cx="48" cy="32" rx="16" ry="16" fill="#E879F9" />
          </svg>
        </div>

        {/** Smaller & Italic H1 **/}
        <h1
          className="text-2xl md:text-4xl italic font-serif font-light mb-2"
          style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}
        >
          Clone a website in seconds
        </h1>

        {/** Tagline **/}
        <p className="text-lg text-white/70 mb-6">
          Start, iterate, and launch your website all in one place
        </p>

        {/** Search/Clone Input **/}
        <form
          onSubmit={handleClone}
          className="relative w-full max-w-2xl mx-auto mb-8"
        >
          <input
            type="url"
            placeholder="Enter URL to clone: https://example.com"
            value={url}
            onChange={handleUrlChange}
            onKeyPress={handleKeyPress}
            className="w-full p-3 pl-5 pr-14 text-base bg-white/5 border border-white/20 rounded-xl text-white placeholder-white/50 outline-none focus:border-purple-500 focus:ring-4 focus:ring-purple-500/10 transition-all"
          />
          <button
            type="submit"
            disabled={status.startsWith("Scraping")}
            className={`
              absolute right-2 top-2 bottom-2 px-4 text-sm 
              bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-lg transition-all
              ${
                status.startsWith("Scraping")
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:shadow-lg hover:shadow-purple-500/25"
              }
            `}
          >
            {status.startsWith("Scraping") ? "⏳" : "Clone"}
          </button>
        </form>

        {/** Status message **/}
        {status && (
          <p
            className={`text-base mb-6 ${
              status.includes("Error")
                ? "text-red-400"
                : status.includes("ready")
                ? "text-green-400"
                : "text-white/70"
            }`}
          >
            {status}
          </p>
        )}
      </div>

      {/** ─────────────────────────────────────────────────────────────── **/}
      {/** Templates Section (unchanged except minor margin adjustments) **/}
      {/** ─────────────────────────────────────────────────────────────── **/}
      <section className="w-full max-w-7xl">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-normal mb-2">
            {/* Websites made with Orchids */}
          </h2>
          <p className="text-white/70 mb-6">
            {/* Click on any one to visit the live site */}
          </p>
{/* 
          <div className="flex flex-wrap justify-center gap-3 mb-6">
            {["Landing Pages", "Portfolio Websites", "Ecommerce Sites"].map(
              (tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg border transition-all text-sm ${
                    activeTab === tab
                      ? "bg-purple-500/20 border-purple-500 text-white"
                      : "bg-white/5 border-white/20 text-white/80 hover:bg-white/10"
                  }`}
                >
                  {tab}
                </button>
              )
            )}
          </div> */}
        </div>

        {/* <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            {
              name: "NOVALAU/NCH",
              category: "Space Technology",
              gradient: "from-gray-800 to-gray-900",
              accent: "ON OUR MISSION",
            },
            {
              name: "SerenityAI",
              category: "AI Therapy",
              gradient: "from-green-700 to-green-800",
              accent: "✓ ✓ ✓",
            },
            {
              name: "SkySwift",
              category: "Drone Delivery",
              gradient: "from-blue-600 to-blue-700",
              accent: "Swift logistics",
            },
            {
              name: "FitTrack",
              category: "Fitness Platform",
              gradient: "from-teal-600 to-teal-700",
              accent: "VITALSYNC",
            },
          ].map((template, index) => (
            <div
              key={template.name}
              className="bg-white/5 border border-white/10 rounded-xl overflow-hidden cursor-pointer hover:transform hover:-translate-y-2 hover:border-purple-500 hover:shadow-2xl hover:shadow-purple-500/20 transition-all duration-300"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={`h-44 bg-gradient-to-br ${template.gradient} relative overflow-hidden`}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-transparent to-purple-500/10"></div>
                <div className="absolute bottom-4 left-4 text-white/80 text-sm font-medium">
                  {template.accent}
                </div>
              </div>
              <div className="p-4">
                <h3 className="text-base font-semibold mb-1">
                  {template.name}
                </h3>
                <p className="text-white/60 text-xs">{template.category}</p>
              </div>
            </div> */}
          {/* ))} */}
        {/* </div> */}
      </section>

      {/** ─────────────────────────────────────────────────────────────── **/}
      {/** Clone Results (unchanged except reduced margin) **/}
      {/** ─────────────────────────────────────────────────────────────── **/}
      {clonedHtml && (
        <section className="w-full max-w-7xl mt-8">
          <div className="bg-white/5 border border-white/10 rounded-xl p-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4">
              <h3 className="text-xl font-semibold mb-2 md:mb-0">
                Cloned Website Preview
              </h3>
              <a
                href={downloadUrl}
                download="cloned.html"
                className="px-4 py-2 text-sm bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-lg hover:shadow-lg hover:shadow-purple-500/25 transition-all"
              >
                📥 Download HTML
              </a>
            </div>
            <div className="border border-white/20 rounded-lg overflow-hidden">
              <iframe
                srcDoc={clonedHtml}
                title="Cloned Preview"
                className="w-full h-[1000px] bg-white"
              />
            </div>
          </div>
        </section>
      )}
    </main>
  );
}


