import React, { useState } from "react";
import { X, Music, Globe, Lock, Loader2, CheckCircle2 } from "lucide-react";
import { playlistService } from "../../api/playlistService";
import { Track } from "../../types/track";

interface ExportPlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultName: string;
  tracksToExport: Track[];
}

export const ExportPlaylistModal = ({
  isOpen,
  onClose,
  defaultName,
  tracksToExport,
}: ExportPlaylistModalProps) => {
  const [name, setName] = useState(defaultName);
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");

  if (!isOpen) return null;

  // ⚡ Mapeo directo de los IDs de MongoDB de los tracks que ya vienen preseleccionados
  const targetTrackIds = tracksToExport.map((t) => t._id);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Guardián de seguridad: El backend rechaza cualquier petición que no tenga exactamente 10 tracks
    if (targetTrackIds.length !== 10) {
      setStatus("error");
      setErrorMessage(
        `Configuración inválida: Se detectaron ${targetTrackIds.length} canciones, pero el sistema requiere exactamente 10.`,
      );
      return;
    }

    setStatus("loading");
    try {
      await playlistService.createPlaylist({
        name,
        description,
        public: isPublic,
        track_ids: targetTrackIds,
      });
      setStatus("success");
      setTimeout(() => {
        setStatus("idle");
        onClose();
      }, 2000);
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err?.message || "Ocurrió un error al exportar la lista.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Cabecera del Modal */}
        <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-green-500">
            <Music className="w-5 h-5" />
            <h3 className="font-bold text-lg text-white">Exportar a Spotify</h3>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Estado de Éxito */}
        {status === "success" ? (
          <div className="p-8 flex flex-col items-center justify-center text-center space-y-3">
            <CheckCircle2 className="w-16 h-16 text-green-500 animate-pulse" />
            <h4 className="text-xl font-bold text-white">¡Playlist Creada!</h4>
            <p className="text-zinc-400 text-sm">
              Ya puedes buscar "{name}" en tu biblioteca de Spotify.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-wider font-bold text-zinc-400 mb-2">
                Nombre de la Playlist
              </label>
              <input
                type="text"
                required
                maxLength={100}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-green-500 transition-colors"
                placeholder="Ej. Mi Mix Enérgico"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider font-bold text-zinc-400 mb-2">
                Descripción (Opcional)
              </label>
              <textarea
                maxLength={500}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2 text-white h-24 resize-none focus:outline-none focus:border-green-500 transition-colors"
                placeholder="Añade detalles sobre este mix personalizado..."
              />
            </div>

            {/* Selector de Visibilidad / Privacidad */}
            <div className="flex items-center justify-between p-3 bg-zinc-800/40 rounded-xl border border-zinc-800">
              <div className="flex items-center gap-3">
                {isPublic ? (
                  <Globe className="text-green-500 w-5 h-5" />
                ) : (
                  <Lock className="text-zinc-400 w-5 h-5" />
                )}
                <div>
                  <p className="text-sm font-semibold text-white">
                    Playlist Pública
                  </p>
                  <p className="text-xs text-zinc-500">
                    Cualquiera en Spotify podrá descubrirla
                  </p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="w-4 h-4 accent-green-500 cursor-pointer"
              />
            </div>

            {/* Etiqueta Informativa de Confirmación de Selección */}
            <p className="text-xs text-zinc-400 text-center bg-zinc-950/50 py-2.5 rounded-xl border border-zinc-800/60">
              🎵 Se exportarán tus **10 canciones seleccionadas** de forma
              directa a tu perfil.
            </p>

            {status === "error" && (
              <p className="text-sm text-red-400 font-medium bg-red-500/10 p-3 rounded-xl border border-red-500/20">
                {errorMessage}
              </p>
            )}

            {/* Botones de Control de Formulario */}
            <div className="pt-2 flex gap-3 justify-end">
              <button
                type="button"
                onClick={onClose}
                disabled={status === "loading"}
                className="px-4 py-2 text-sm font-semibold text-zinc-400 hover:text-white transition-colors disabled:opacity-40"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={status === "loading"}
                className="bg-green-600 hover:bg-green-500 text-white font-bold text-sm px-6 py-2.5 rounded-full transition-all flex items-center gap-2 shadow-lg hover:scale-102 active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {status === "loading" ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Exportando...
                  </>
                ) : (
                  "Guardar en Spotify"
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
